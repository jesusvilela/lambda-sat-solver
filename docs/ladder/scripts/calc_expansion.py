import json

with open('benchmark_206_results.json') as f:
    r = json.load(f)

fams = {}
for x in r:
    fam = x['family']
    if fam not in fams:
        fams[fam] = {'exp': 0, 'count': 0, 'methods': set(), 't_cdcl': 0, 't_mw': 0}
    
    t_k = x['kissat_s'] if x['kissat'] != 'TIMEOUT' else 20.0
    t_c = x['cadical_s'] if x['cadical'] != 'TIMEOUT' else 20.0
    t_m = x['middleware_s'] if x['middleware'] != 'TIMEOUT' else 20.0
    
    best_cdcl = min(t_k, t_c)
    exp = best_cdcl - t_m
    
    fams[fam]['exp'] += exp
    fams[fam]['t_cdcl'] += best_cdcl
    fams[fam]['t_mw'] += t_m
    fams[fam]['count'] += 1
    fams[fam]['methods'].add(x['solved_by'])

print("§[EVALUATION FRAME]")
for fam, d in fams.items():
    print(f"Family: {fam} | Instances: {d['count']} | "
          f"Affordance Expansion: {d['exp']:.2f}s "
          f"(CDCL_min: {d['t_cdcl']:.2f}s -> MW: {d['t_mw']:.2f}s) | "
          f"Sheath Resonance: {d['methods']}")
