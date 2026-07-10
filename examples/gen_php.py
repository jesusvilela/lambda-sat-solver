import sys

def generate_php(n, out_path):
    holes = n - 1
    
    def var(p, h):
        return p * holes + h + 1
        
    clauses = []
    
    # Each pigeon is in at least one hole
    for p in range(n):
        clause = [var(p, h) for h in range(holes)]
        clauses.append(clause)
        
    # No two pigeons are in the same hole
    for h in range(holes):
        for p1 in range(n):
            for p2 in range(p1 + 1, n):
                clauses.append([-var(p1, h), -var(p2, h)])
                
    with open(out_path, 'w') as f:
        f.write(f"p cnf {n * holes} {len(clauses)}\n")
        for clause in clauses:
            f.write(" ".join(map(str, clause)) + " 0\n")

if __name__ == "__main__":
    n = int(sys.argv[1])
    generate_php(n, sys.argv[2])
