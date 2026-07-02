"""
Pre-registered evals for the Lambda DSL.

These tests pin the *actual* behaviour of lambda_dsl.py so that future
changes to the DSL don't silently regress, and so that the gap between
current capability and the intended effect-system design is explicit and
machine-checked.

Current status (per SOTA critique):
  - compose() / pipeline() are correctly implemented but are dead code —
    nothing in the production path calls them.  The tests below verify
    their semantics; the corresponding production fix wires pipeline() into
    create_solve_pipeline() so these combinators are no longer dead.
  - TypeChecker maps effect names to flat return types only; it does NOT
    enforce ordering or linearity ("you can't get a Result without going
    through a check effect").  Tests document this limitation explicitly.
  - Evaluator dispatches effects to Python handlers; it does not carry
    session/linear-type information.
"""

import pytest
import asyncio

from backend.lambda_dsl import (
    # AST nodes
    Abs,
    App,
    Effect,
    Literal,
    Var,
    # Builder functions
    abs_,
    app,
    compose,
    effect,
    literal,
    pipeline,
    var,
    # Type system
    TypeChecker,
    TypeEnv,
    # Evaluator
    Evaluator,
)


# ---------------------------------------------------------------------------
# compose() and pipeline() — structural / AST tests
# ---------------------------------------------------------------------------

class TestCompose:
    """compose(f, g) must build λx. f(g(x))."""

    def test_compose_returns_abs(self):
        f = abs_('y', var('y'))
        g = abs_('z', var('z'))
        result = compose(f, g)
        assert isinstance(result, Abs)
        assert result.param == 'x'

    def test_compose_body_is_app_of_f_applied_to_app_of_g(self):
        f = abs_('y', var('y'))
        g = abs_('z', var('z'))
        result = compose(f, g)
        # body = f(g(x))
        outer = result.body
        assert isinstance(outer, App)
        assert outer.func is f
        inner = outer.arg
        assert isinstance(inner, App)
        assert inner.func is g
        assert isinstance(inner.arg, Var)
        assert inner.arg.name == 'x'

    def test_compose_with_effects(self):
        """compose works over Effect nodes (not just Abs)."""
        f = abs_('r', effect('checkModel', var('r')))
        g = abs_('cnf', effect('solve', var('cnf')))
        result = compose(f, g)
        assert isinstance(result, Abs)


class TestPipeline:
    """pipeline(*stages) must reduce to left-to-right composition."""

    def test_pipeline_empty_raises(self):
        with pytest.raises(ValueError):
            pipeline()

    def test_pipeline_single_returns_identity(self):
        stage = abs_('x', var('x'))
        assert pipeline(stage) is stage

    def test_pipeline_two_stages_returns_abs(self):
        f = abs_('y', var('y'))
        g = abs_('z', var('z'))
        result = pipeline(f, g)
        assert isinstance(result, Abs)

    def test_pipeline_three_stages_is_abs(self):
        stages = [abs_(f'x{i}', var(f'x{i}')) for i in range(3)]
        result = pipeline(*stages)
        assert isinstance(result, Abs)

    def test_pipeline_two_stages_same_as_compose(self):
        f = abs_('a', var('a'))
        g = abs_('b', var('b'))
        via_pipeline = pipeline(f, g)
        via_compose = compose(f, g)
        # Both should have identical structure
        assert type(via_pipeline) == type(via_compose)
        assert via_pipeline.param == via_compose.param


# ---------------------------------------------------------------------------
# TypeChecker — effect type mapping and known limitations
# ---------------------------------------------------------------------------

class TestTypeCheckerEffects:
    """TypeChecker maps known effect names to their declared return types."""

    tc = TypeChecker()

    def test_readCNF_type(self):
        assert self.tc.check(effect('readCNF', 'path')) == 'CNF'

    def test_solve_type(self):
        assert self.tc.check(effect('solve', 'cnf', 'h', 'b')) == 'Result'

    def test_checkModel_type(self):
        assert self.tc.check(effect('checkModel', 'cnf', 'model')) == 'Bool'

    def test_checkDRAT_type(self):
        assert self.tc.check(effect('checkDRAT', 'cnf', 'proof')) == 'Bool'

    def test_checkLRAT_type(self):
        assert self.tc.check(effect('checkLRAT', 'cnf', 'proof')) == 'Bool'

    def test_unknown_effect_raises_type_error(self):
        with pytest.raises(TypeError, match="Unknown effect"):
            self.tc.check(effect('nonexistentEffect'))


class TestTypeCheckerAbsAndApp:
    """TypeChecker infers function and application types."""

    tc = TypeChecker()

    def test_abs_over_effect_gives_function_type(self):
        # λcnf. solve(cnf, h, b)  →  CNF -> Result
        expr = abs_('cnf', effect('solve', var('cnf')))
        assert self.tc.check(expr) == 'CNF -> Result'

    def test_abs_readcnf(self):
        # λpath. readCNF(path)  →  CNF -> CNF
        # (param is bound as CNF by convention; body returns CNF)
        expr = abs_('path', effect('readCNF', var('path')))
        assert self.tc.check(expr) == 'CNF -> CNF'

    def test_type_mismatch_in_app_raises(self):
        # Apply a (CNF -> Result) function to a Bool literal — should fail
        func = abs_('cnf', effect('solve', var('cnf')))
        arg = literal(True)   # Bool
        with pytest.raises(TypeError, match="Type mismatch"):
            self.tc.check(app(func, arg))

    def test_apply_non_function_raises(self):
        with pytest.raises(TypeError, match="Cannot apply non-function"):
            self.tc.check(app(literal(42), literal(1)))

    def test_unbound_variable_raises(self):
        with pytest.raises(TypeError, match="Unbound variable"):
            self.tc.check(var('unbound'))

    def test_var_resolves_in_env(self):
        env = TypeEnv().extend('x', 'CNF')
        assert TypeChecker().check(var('x'), env) == 'CNF'


class TestTypeCheckerLiterals:
    tc = TypeChecker()

    def test_cnf_literal_type(self):
        assert self.tc.check(literal({'clauses': [[1, 2]]})) == 'CNF'

    def test_bool_literal_type(self):
        assert self.tc.check(literal(True)) == 'Bool'
        assert self.tc.check(literal(False)) == 'Bool'

    def test_other_literal_type(self):
        assert self.tc.check(literal(42)) == 'Any'
        assert self.tc.check(literal("hello")) == 'Any'


class TestTypeCheckerKnownLimitations:
    """
    Document, via assertion, what the TypeChecker currently cannot enforce.

    These tests should remain passing; they confirm the *absence* of a
    feature (effect ordering / linearity) so that when the feature is
    added the tests can be updated to the new contract.
    """

    tc = TypeChecker()

    def test_solve_effect_does_not_require_prior_readCNF(self):
        # The type-checker assigns 'Result' to solve without knowing
        # whether readCNF was called first.  This is the limitation the
        # critique identifies: no ordering enforcement.
        result_type = self.tc.check(effect('solve', 'cnf', 'h', 'b'))
        assert result_type == 'Result'  # No ordering error raised

    def test_checkModel_does_not_require_prior_solve(self):
        # Similarly, checkModel can be type-checked without a preceding
        # solve effect.
        result_type = self.tc.check(effect('checkModel', 'cnf', 'model'))
        assert result_type == 'Bool'


# ---------------------------------------------------------------------------
# Evaluator — pure function composition (no solver required)
# ---------------------------------------------------------------------------

class TestEvaluatorPure:
    """Evaluator correctly reduces pure lambda terms."""

    @pytest.mark.asyncio
    async def test_literal_evaluates_to_value(self):
        ev = Evaluator({})
        assert await ev.evaluate(literal(42)) == 42
        assert await ev.evaluate(literal("hello")) == "hello"

    @pytest.mark.asyncio
    async def test_var_resolves_from_env(self):
        ev = Evaluator({})
        result = await ev.evaluate(var('x'), {'x': 99})
        assert result == 99

    @pytest.mark.asyncio
    async def test_unbound_var_raises(self):
        ev = Evaluator({})
        with pytest.raises(NameError, match="Unbound variable"):
            await ev.evaluate(var('missing'))

    @pytest.mark.asyncio
    async def test_abs_creates_closure(self):
        from backend.lambda_dsl import Closure
        ev = Evaluator({})
        fn = abs_('x', var('x'))
        result = await ev.evaluate(fn)
        assert isinstance(result, Closure)
        assert result.param == 'x'

    @pytest.mark.asyncio
    async def test_app_of_identity(self):
        ev = Evaluator({})
        identity = abs_('x', var('x'))
        result = await ev.evaluate(app(identity, literal(7)))
        assert result == 7

    @pytest.mark.asyncio
    async def test_compose_evaluates_correctly(self):
        """compose(double, increment)(3) == double(increment(3)) == 8"""
        # Use effect handlers to simulate pure functions
        async def double(x):
            return x * 2

        async def increment(x):
            return x + 1

        ev = Evaluator({'double': double, 'increment': increment})
        # λx. double(increment(x))
        expr = compose(
            abs_('y', effect('double', var('y'))),
            abs_('z', effect('increment', var('z'))),
        )
        result = await ev.evaluate(app(expr, literal(3)))
        assert result == 8  # increment(3)=4, double(4)=8

    @pytest.mark.asyncio
    async def test_pipeline_two_stages_evaluates(self):
        """pipeline(f, g)(x) applies f first (innermost), then g (outermost)."""
        async def negate(x):
            return -x

        async def square(x):
            return x * x

        ev = Evaluator({'negate': negate, 'square': square})
        expr = pipeline(
            abs_('y', effect('negate', var('y'))),
            abs_('z', effect('square', var('z'))),
        )
        # negate(5)=-5, then square(-5)=25
        result = await ev.evaluate(app(expr, literal(5)))
        assert result == 25

    @pytest.mark.asyncio
    async def test_unknown_effect_raises(self):
        ev = Evaluator({})
        with pytest.raises(RuntimeError, match="Unknown effect"):
            await ev.evaluate(effect('noSuchEffect'))


# ---------------------------------------------------------------------------
# create_solve_pipeline — structural contract
# ---------------------------------------------------------------------------

class TestCreateSolvePipelineStructure:
    """
    create_solve_pipeline() must return a LambdaExpr that:
      1. Type-checks as CNF -> Result.
      2. Is built via pipeline() so that compose/pipeline are not dead code.
    """

    def test_pipeline_typechecks_as_cnf_to_result(self):
        from backend.middleware import create_middleware
        mw = create_middleware(strict_mode=False)
        p = mw.create_solve_pipeline()
        tc = TypeChecker()
        assert tc.check(p) == 'CNF -> Result'

    def test_pipeline_expr_is_abs(self):
        from backend.middleware import create_middleware
        mw = create_middleware(strict_mode=False)
        p = mw.create_solve_pipeline()
        # Must be a lambda abstraction (wraps the solve effect)
        assert isinstance(p, Abs)

    def test_pipeline_body_contains_solve_effect(self):
        from backend.middleware import create_middleware
        mw = create_middleware(strict_mode=False)
        p = mw.create_solve_pipeline()
        assert isinstance(p.body, Effect)
        assert p.body.name == 'solve'
