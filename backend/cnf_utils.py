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


def tseitin_transform(formula_ast: dict) -> CNFFormula:
    """
    Tseitin transformation with projection (equisatisfiable CNF)

    This is a simplified version - for MVP we'll just handle basic formulas.
    In production, this would handle full propositional logic with proper
    Tseitin transformation.
    """
    # For now, assume input is already in CNF format
    # This is a placeholder for the full Tseitin implementation
    if 'clauses' in formula_ast:
        return CNFFormula(
            num_vars=formula_ast.get('variables', 0),
            clauses=formula_ast['clauses']
        )

    # TODO: Implement full Tseitin transformation for arbitrary formulas
    raise NotImplementedError(
        "Full Tseitin transformation not yet implemented. "
        "Input formula must already be in CNF format."
    )
