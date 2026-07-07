"""
Lambda DSL for SAT solver middleware — the *pipeline* language.

Implements a typed lambda calculus with effect tracking, used to compose
solve/verify *pipelines* (see `middleware.py`). This is the orchestration DSL.

Not to be confused with `lambda_sat.py`, the *object-level* Lambda ⊗ SAT fusion,
where a Boolean lambda term is itself the thing being decided. Neither module is
on the critical solving path — both are research artifacts — but they are
distinct: this one describes *how to run* a solve; `lambda_sat` treats a lambda
term *as* a SAT instance.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class ExprType(Enum):
    """Expression types in the lambda DSL"""
    VAR = "var"
    APP = "app"
    ABS = "abs"
    EFFECT = "effect"
    LITERAL = "literal"


@dataclass
class LambdaExpr:
    """Base class for lambda expressions"""
    expr_type: ExprType


@dataclass
class Var(LambdaExpr):
    """Variable reference"""
    name: str

    def __init__(self, name: str):
        super().__init__(ExprType.VAR)
        self.name = name


@dataclass
class App(LambdaExpr):
    """Function application"""
    func: LambdaExpr
    arg: LambdaExpr

    def __init__(self, func: LambdaExpr, arg: LambdaExpr):
        super().__init__(ExprType.APP)
        self.func = func
        self.arg = arg


@dataclass
class Abs(LambdaExpr):
    """Lambda abstraction"""
    param: str
    body: LambdaExpr

    def __init__(self, param: str, body: LambdaExpr):
        super().__init__(ExprType.ABS)
        self.param = param
        self.body = body


@dataclass
class Effect(LambdaExpr):
    """Side effect operation"""
    name: str
    args: List[Any]

    def __init__(self, name: str, args: List[Any]):
        super().__init__(ExprType.EFFECT)
        self.name = name
        self.args = args


@dataclass
class Literal(LambdaExpr):
    """Literal value"""
    value: Any

    def __init__(self, value: Any):
        super().__init__(ExprType.LITERAL)
        self.value = value


class TypeEnv:
    """Type environment for type checking"""

    def __init__(self):
        self.env: Dict[str, str] = {}

    def extend(self, var: str, typ: str) -> 'TypeEnv':
        """Create new environment with variable binding"""
        new_env = TypeEnv()
        new_env.env = self.env.copy()
        new_env.env[var] = typ
        return new_env

    def lookup(self, var: str) -> Optional[str]:
        """Look up variable type"""
        return self.env.get(var)


class TypeChecker:
    """Type checker for lambda expressions"""

    #: name -> (expected arg types, return type). 'Any' matches anything
    #: (used for opaque literal payloads like heuristic/budget dicts, which
    #: the Literal-type-inference below can't type more precisely without a
    #: richer value-type system than this DSL has).
    EFFECT_SIGNATURES = {
        'readCNF': (['Any'], 'CNF'),
        'solve': (['CNF', 'Any', 'Any'], 'Result'),
        'checkModel': (['CNF', 'Any'], 'Bool'),
        'checkDRAT': (['CNF', 'Any'], 'Bool'),
        'checkLRAT': (['CNF', 'Any'], 'Bool'),
        'profileCNF': (['CNF'], 'Profile'),
        'selectHeuristic': (['Profile'], 'Config'),
        'solveWithConfig': (['CNF', 'Config'], 'Result'),
        'certify': (['Result'], 'Certificate'),
    }

    #: Derived name -> return-type view, kept for readability/back-compat
    #: with anything that only wants the return type.
    EFFECT_TYPES = {name: sig[1] for name, sig in EFFECT_SIGNATURES.items()}

    #: nesting cap for `check`, well below CPython's recursion limit, so a
    #: pathologically deep composition fails with a clean TypeError instead of
    #: an uncatchable RecursionError / stack overflow (latent until a
    #: same-type-chainable effect signature is added; guarded now regardless).
    MAX_DEPTH = 400

    def check(self, expr: LambdaExpr, env: Optional[TypeEnv] = None,
              _depth: int = 0) -> str:
        """Type check an expression and return its type"""
        if env is None:
            env = TypeEnv()
        if _depth > self.MAX_DEPTH:
            raise TypeError(
                f"expression nesting exceeds MAX_DEPTH ({self.MAX_DEPTH})")
        _depth += 1

        if isinstance(expr, Var):
            typ = env.lookup(expr.name)
            if typ is None:
                raise TypeError(f"Unbound variable: {expr.name}")
            return typ

        elif isinstance(expr, Abs):
            # Assume CNF input for simplicity
            new_env = env.extend(expr.param, 'CNF')
            body_type = self.check(expr.body, new_env, _depth)
            return f"CNF -> {body_type}"

        elif isinstance(expr, App):
            func_type = self.check(expr.func, env, _depth)
            arg_type = self.check(expr.arg, env, _depth)

            # Parse function type
            if ' -> ' in func_type:
                parts = func_type.split(' -> ', 1)
                expected_arg = parts[0]
                return_type = parts[1]

                if expected_arg != arg_type:
                    raise TypeError(
                        f"Type mismatch: expected {expected_arg}, got {arg_type}"
                    )
                return return_type
            else:
                raise TypeError(f"Cannot apply non-function type: {func_type}")

        elif isinstance(expr, Effect):
            if expr.name not in self.EFFECT_SIGNATURES:
                raise TypeError(f"Unknown effect: {expr.name}")
            expected_arg_types, return_type = self.EFFECT_SIGNATURES[expr.name]
            if len(expr.args) != len(expected_arg_types):
                raise TypeError(
                    f"Effect {expr.name!r} expects {len(expected_arg_types)} "
                    f"argument(s), got {len(expr.args)}"
                )
            # Recurse into nested-expression args so a composed pipeline
            # (effect(a, effect(b, effect(c, var(x))))) gets its inner
            # stages checked, AND validate each argument's actual type
            # against what this effect expects - this is what catches a
            # composition like certify(profileCNF(cnf)) (skipping
            # selectHeuristic/solveWithConfig): certify expects 'Result',
            # profileCNF produces 'Profile', mismatch, rejected below.
            for arg, expected in zip(expr.args, expected_arg_types):
                actual = (self.check(arg, env, _depth)
                          if isinstance(arg, LambdaExpr) else 'Any')
                if expected != 'Any' and actual != 'Any' and actual != expected:
                    raise TypeError(
                        f"Effect {expr.name!r}: argument type mismatch - "
                        f"expected {expected}, got {actual}"
                    )
            return return_type

        elif isinstance(expr, Literal):
            # Infer type from value
            if isinstance(expr.value, dict) and 'clauses' in expr.value:
                return 'CNF'
            elif isinstance(expr.value, bool):
                return 'Bool'
            else:
                return 'Any'

        raise TypeError(f"Unknown expression type: {type(expr)}")


class Closure:
    """Closure for lambda abstraction"""

    def __init__(self, param: str, body: LambdaExpr, env: Dict[str, Any]):
        self.param = param
        self.body = body
        self.env = env.copy()


class Evaluator:
    """Evaluator for lambda expressions"""

    def __init__(self, effect_handlers: Dict[str, Any]):
        self.effect_handlers = effect_handlers

    async def evaluate(
        self,
        expr: LambdaExpr,
        env: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Evaluate an expression"""
        if env is None:
            env = {}

        if isinstance(expr, Var):
            if expr.name not in env:
                raise NameError(f"Unbound variable: {expr.name}")
            return env[expr.name]

        elif isinstance(expr, Abs):
            return Closure(expr.param, expr.body, env)

        elif isinstance(expr, App):
            func = await self.evaluate(expr.func, env)
            arg = await self.evaluate(expr.arg, env)

            if isinstance(func, Closure):
                new_env = func.env.copy()
                new_env[func.param] = arg
                return await self.evaluate(func.body, new_env)
            else:
                raise TypeError("Cannot apply non-function")

        elif isinstance(expr, Effect):
            return await self.execute_effect(expr.name, expr.args, env)

        elif isinstance(expr, Literal):
            return expr.value

        raise ValueError(f"Unknown expression type: {type(expr)}")

    async def execute_effect(
        self,
        name: str,
        args: List[Any],
        env: Dict[str, Any]
    ) -> Any:
        """Execute a side effect"""
        if name not in self.effect_handlers:
            raise RuntimeError(f"Unknown effect: {name}")

        handler = self.effect_handlers[name]

        # Evaluate arguments if they are expressions
        evaluated_args = []
        for arg in args:
            if isinstance(arg, LambdaExpr):
                evaluated_args.append(await self.evaluate(arg, env))
            else:
                evaluated_args.append(arg)

        return await handler(*evaluated_args)


# DSL builder functions
def var(name: str) -> Var:
    """Create variable reference"""
    return Var(name)


def abs_(param: str, body: LambdaExpr) -> Abs:
    """Create lambda abstraction"""
    return Abs(param, body)


def app(func: LambdaExpr, arg: LambdaExpr) -> App:
    """Create function application"""
    return App(func, arg)


def effect(name: str, *args: Any) -> Effect:
    """Create effect"""
    return Effect(name, list(args))


def literal(value: Any) -> Literal:
    """Create literal value"""
    return Literal(value)


def compose(f: LambdaExpr, g: LambdaExpr) -> LambdaExpr:
    """Compose two functions: f ∘ g"""
    return abs_('x', app(f, app(g, var('x'))))


def pipeline(*stages: LambdaExpr) -> LambdaExpr:
    """Create a pipeline of function stages"""
    if len(stages) == 0:
        raise ValueError("Pipeline requires at least one stage")
    if len(stages) == 1:
        return stages[0]

    result = stages[0]
    for stage in stages[1:]:
        result = compose(stage, result)
    return result
