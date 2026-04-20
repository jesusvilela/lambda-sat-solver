"""
CNF formula utilities and DIMACS parser
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from pathlib import Path


@dataclass
class CNFFormula:
    """CNF formula representation"""
    num_vars: int
    clauses: List[List[int]]
    comments: List[str] = None

    def __post_init__(self):
        if self.comments is None:
            self.comments = []

    @property
    def num_clauses(self) -> int:
        return len(self.clauses)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'variables': self.num_vars,
            'clauses': self.clauses,
            'num_clauses': self.num_clauses
        }


def parse_dimacs(text: str) -> CNFFormula:
    """
    Parse DIMACS CNF format

    Format:
        c Comment lines
        p cnf <num_vars> <num_clauses>
        <lit1> <lit2> ... 0
    """
    lines = text.strip().split('\n')
    comments = []
    num_vars = 0
    num_clauses_declared = 0
    clauses = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('c'):
            comments.append(line[1:].strip())
        elif line.startswith('p cnf'):
            parts = line.split()
            if len(parts) >= 4:
                num_vars = int(parts[2])
                num_clauses_declared = int(parts[3])
        else:
            # Parse clause
            literals = [int(x) for x in line.split() if x]
            # Remove trailing 0
            if literals and literals[-1] == 0:
                literals = literals[:-1]
            if literals:
                clauses.append(literals)

    if num_vars == 0:
        # Infer number of variables from clauses
        max_var = 0
        for clause in clauses:
            for lit in clause:
                max_var = max(max_var, abs(lit))
        num_vars = max_var

    return CNFFormula(
        num_vars=num_vars,
        clauses=clauses,
        comments=comments
    )


def parse_dimacs_file(path: Path) -> CNFFormula:
    """Parse DIMACS CNF file"""
    with open(path, 'r') as f:
        return parse_dimacs(f.read())


def write_dimacs(formula: CNFFormula, path: Path):
    """Write CNF formula to DIMACS file"""
    with open(path, 'w') as f:
        # Write comments
        for comment in formula.comments:
            f.write(f"c {comment}\n")

        # Write header
        f.write(f"p cnf {formula.num_vars} {formula.num_clauses}\n")

        # Write clauses
        for clause in formula.clauses:
            clause_str = ' '.join(str(lit) for lit in clause)
            f.write(f"{clause_str} 0\n")


def verify_model(formula: CNFFormula, model: Dict[int, bool]) -> bool:
    """
    Verify that a model satisfies the CNF formula

    Args:
        formula: CNF formula to check
        model: Variable assignments (1-indexed)

    Returns:
        True if model satisfies all clauses, False otherwise
    """
    for clause in formula.clauses:
        clause_satisfied = False

        for literal in clause:
            var = abs(literal)
            value = model.get(var)

            if value is None:
                # Unassigned variable - cannot verify
                continue

            # Check if literal is satisfied
            literal_value = value if literal > 0 else not value
            if literal_value:
                clause_satisfied = True
                break

        if not clause_satisfied:
            return False

    return True


def parse_model_line(line: str) -> Dict[int, bool]:
    """
    Parse a model from SAT solver output line

    Format: "v 1 -2 3 0" or just "1 -2 3 0"
    """
    model = {}

    # Remove 'v' prefix if present
    if line.strip().startswith('v'):
        line = line[1:]

    for token in line.split():
        token = token.strip()
        if not token or token == '0':
            continue

        lit = int(token)
        var = abs(lit)
        value = lit > 0

        model[var] = value

    return model


def format_model(model: Dict[int, bool]) -> str:
    """Format model as space-separated literals"""
    literals = []
    for var in sorted(model.keys()):
        lit = var if model[var] else -var
        literals.append(str(lit))
    return ' '.join(literals) + ' 0'


class TseitinTransformer:
    """
    Full Tseitin transformation for propositional formulas

    Converts arbitrary propositional formulas to equisatisfiable CNF.
    Supports: AND, OR, NOT, IMPLIES, IFF, XOR, LITERAL
    """

    def __init__(self):
        self.next_var = 1
        self.clauses = []
        self.var_map = {}  # Maps subformula hashes to Tseitin variables

    def fresh_var(self) -> int:
        """Allocate a fresh Tseitin variable"""
        var = self.next_var
        self.next_var += 1
        return var

    def transform(self, formula: dict, top_vars: Optional[Set[int]] = None) -> CNFFormula:
        """
        Transform formula to CNF using Tseitin transformation

        Args:
            formula: Formula AST with structure:
                {'type': 'AND'|'OR'|'NOT'|'IMPLIES'|'IFF'|'XOR'|'LITERAL',
                 'children': [...] or 'value': int}
            top_vars: Set of top-level variables (for projection)
                     If provided, only these variables appear in the original formula

        Returns:
            Equisatisfiable CNF formula

        Formula AST format:
            Literal: {'type': 'LITERAL', 'value': 1}  (positive literal)
                    {'type': 'LITERAL', 'value': -1} (negative literal)
            NOT: {'type': 'NOT', 'child': <formula>}
            AND: {'type': 'AND', 'children': [<formula>, ...]}
            OR: {'type': 'OR', 'children': [<formula>, ...]}
            IMPLIES: {'type': 'IMPLIES', 'left': <formula>, 'right': <formula>}
            IFF: {'type': 'IFF', 'left': <formula>, 'right': <formula>}
            XOR: {'type': 'XOR', 'left': <formula>, 'right': <formula>}
        """
        self.clauses = []
        self.var_map = {}

        # Determine maximum variable in input formula
        max_var = self._find_max_var(formula)
        self.next_var = max_var + 1

        # Transform formula and get top-level variable
        top_var = self._transform_formula(formula)

        # Add unit clause forcing top variable to be true
        self.clauses.append([top_var])

        return CNFFormula(
            num_vars=self.next_var - 1,
            clauses=self.clauses,
            comments=[f"Generated by Tseitin transformation"]
        )

    def _find_max_var(self, formula: dict) -> int:
        """Find maximum variable number in formula"""
        if formula['type'] == 'LITERAL':
            return abs(formula['value'])
        elif formula['type'] == 'NOT':
            return self._find_max_var(formula['child'])
        elif formula['type'] in ['AND', 'OR']:
            return max((self._find_max_var(child) for child in formula['children']), default=0)
        elif formula['type'] in ['IMPLIES', 'IFF', 'XOR']:
            return max(self._find_max_var(formula['left']),
                      self._find_max_var(formula['right']))
        return 0

    def _transform_formula(self, formula: dict) -> int:
        """
        Transform formula and return the Tseitin variable representing it

        Returns:
            Variable number representing this formula
        """
        formula_type = formula['type']

        if formula_type == 'LITERAL':
            # Base case: literal is already a variable
            return formula['value']

        # Create unique key for memoization
        formula_key = str(formula)
        if formula_key in self.var_map:
            return self.var_map[formula_key]

        # Allocate fresh variable for this subformula
        tseitin_var = self.fresh_var()
        self.var_map[formula_key] = tseitin_var

        if formula_type == 'NOT':
            child_var = self._transform_formula(formula['child'])
            # tseitin_var <-> NOT child_var
            # Equivalent to: (tseitin_var OR child_var) AND (NOT tseitin_var OR NOT child_var)
            self.clauses.append([tseitin_var, child_var])
            self.clauses.append([-tseitin_var, -child_var])

        elif formula_type == 'AND':
            child_vars = [self._transform_formula(child) for child in formula['children']]
            # tseitin_var <-> AND(child_vars)
            # tseitin_var -> child_i for all i: (NOT tseitin_var OR child_i)
            for child_var in child_vars:
                self.clauses.append([-tseitin_var, child_var])
            # AND(child_i) -> tseitin_var: (NOT child_1 OR ... OR NOT child_n OR tseitin_var)
            self.clauses.append([-v for v in child_vars] + [tseitin_var])

        elif formula_type == 'OR':
            child_vars = [self._transform_formula(child) for child in formula['children']]
            # tseitin_var <-> OR(child_vars)
            # child_i -> tseitin_var for all i: (NOT child_i OR tseitin_var)
            for child_var in child_vars:
                self.clauses.append([-child_var, tseitin_var])
            # tseitin_var -> OR(child_i): (NOT tseitin_var OR child_1 OR ... OR child_n)
            self.clauses.append([-tseitin_var] + child_vars)

        elif formula_type == 'IMPLIES':
            # A -> B is equivalent to (NOT A) OR B
            left_var = self._transform_formula(formula['left'])
            right_var = self._transform_formula(formula['right'])
            # tseitin_var <-> (left_var -> right_var)
            # tseitin_var <-> (NOT left_var OR right_var)

            # tseitin_var -> (NOT left_var OR right_var):
            #   (NOT tseitin_var OR NOT left_var OR right_var)
            self.clauses.append([-tseitin_var, -left_var, right_var])

            # (NOT left_var OR right_var) -> tseitin_var:
            #   (left_var OR tseitin_var) AND (NOT right_var OR tseitin_var)
            self.clauses.append([left_var, tseitin_var])
            self.clauses.append([-right_var, tseitin_var])

        elif formula_type == 'IFF':
            # A <-> B is equivalent to (A -> B) AND (B -> A)
            left_var = self._transform_formula(formula['left'])
            right_var = self._transform_formula(formula['right'])
            # tseitin_var <-> (left_var <-> right_var)

            # tseitin_var -> (left_var <-> right_var):
            #   (NOT tseitin_var OR NOT left_var OR right_var) AND
            #   (NOT tseitin_var OR left_var OR NOT right_var)
            self.clauses.append([-tseitin_var, -left_var, right_var])
            self.clauses.append([-tseitin_var, left_var, -right_var])

            # (left_var <-> right_var) -> tseitin_var:
            #   (NOT left_var OR NOT right_var OR tseitin_var) AND
            #   (left_var OR right_var OR tseitin_var)
            self.clauses.append([-left_var, -right_var, tseitin_var])
            self.clauses.append([left_var, right_var, tseitin_var])

        elif formula_type == 'XOR':
            # A XOR B is equivalent to (A OR B) AND (NOT A OR NOT B)
            left_var = self._transform_formula(formula['left'])
            right_var = self._transform_formula(formula['right'])
            # tseitin_var <-> (left_var XOR right_var)

            # tseitin_var -> (left_var XOR right_var):
            #   (NOT tseitin_var OR left_var OR right_var) AND
            #   (NOT tseitin_var OR NOT left_var OR NOT right_var)
            self.clauses.append([-tseitin_var, left_var, right_var])
            self.clauses.append([-tseitin_var, -left_var, -right_var])

            # (left_var XOR right_var) -> tseitin_var:
            #   (NOT left_var OR NOT right_var OR tseitin_var) AND
            #   (left_var OR right_var OR tseitin_var)
            self.clauses.append([-left_var, -right_var, tseitin_var])
            self.clauses.append([left_var, right_var, tseitin_var])

        else:
            raise ValueError(f"Unknown formula type: {formula_type}")

        return tseitin_var


def tseitin_transform(formula_ast: dict) -> CNFFormula:
    """
    Tseitin transformation with projection (equisatisfiable CNF)

    Converts arbitrary propositional formulas to CNF using Tseitin transformation.

    Args:
        formula_ast: Formula AST or CNF dict

    Returns:
        Equisatisfiable CNF formula
    """
    # If already in CNF format, return as-is
    if 'clauses' in formula_ast:
        return CNFFormula(
            num_vars=formula_ast.get('variables', 0),
            clauses=formula_ast['clauses']
        )

    # If it's a formula AST, apply Tseitin transformation
    if 'type' in formula_ast:
        transformer = TseitinTransformer()
        return transformer.transform(formula_ast)

    raise ValueError(
        "Invalid formula format. Must be either CNF dict or formula AST."
    )
