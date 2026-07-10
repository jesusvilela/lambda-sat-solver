import json
import urllib.request
import urllib.error
import random
import os
import sys

LM_STUDIO_URL = "http://192.168.56.1:1234/v1/chat/completions"
MODEL = "google/gemma-4-12b"

# ---------------------------------------------------------
# Phase 2: Active Learning Benchmark Oracle
# ---------------------------------------------------------

def load_dataset(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data

def active_learning_sample(data, sample_size=20):
    """
    Selects a diverse subset of instances to approximate full PAR-2.
    Information-gain sampling proxy: we stratify across families and select
    hard/easy instances to maximize entropy reduction.
    """
    families = {}
    for row in data:
        fam = row.get('family', 'mixed')
        if fam not in families:
            families[fam] = []
        families[fam].append(row)
        
    sampled = []
    # Take equal numbers from each family, prioritizing extremes (fastest/slowest)
    per_family = max(1, sample_size // len(families))
    for fam, insts in families.items():
        # Sort by total time to find extremes
        sorted_insts = sorted(insts, key=lambda x: float(x.get('times', {}).get('total', 0)))
        if len(sorted_insts) <= per_family:
            sampled.extend(sorted_insts)
        else:
            # Pick easiest, hardest, and random in between
            sampled.append(sorted_insts[0])
            sampled.append(sorted_insts[-1])
            if per_family > 2:
                sampled.extend(random.sample(sorted_insts[1:-1], per_family - 2))
                
    # Truncate if we overshot due to rounding
    return sampled[:sample_size]

def evaluate_heuristic_on_sample(heuristic_code, sample):
    """
    Evaluates the dynamically generated python `choose_heuristic` on the AL sample.
    (Mocked out for now, to be integrated with actual benchmark runner)
    """
    # Write the heuristic code to policy.py
    policy_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'policy.py')
    with open(policy_path, 'r') as f:
        original_policy = f.read()
        
    # Replace the choose_heuristic function
    import re
    # We will just write a simple regex replacement or exact string replacement
    new_policy = re.sub(r'def choose_heuristic.*?return AGGRESSIVE', heuristic_code, original_policy, flags=re.DOTALL)
    
    with open(policy_path, 'w') as f:
        f.write(new_policy)
        
    # Run benchmark_cli.py on the sample
    # Here we would invoke the benchmark tool and compute PAR-2.
    # We will implement this as a subprocess call later.
    
    # Restore policy
    with open(policy_path, 'w') as f:
        f.write(original_policy)
        
    # Return a dummy PAR-2 score for now
    return random.uniform(10.0, 50.0)


# ---------------------------------------------------------
# Phase 3: AutoModSAT Evolutionary Loop
# ---------------------------------------------------------

def query_llm(prompt, temperature=0.7):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a SAT solver expert interacting via §-LANG. Output ONLY valid python code."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": 2048
    }
    
    req = urllib.request.Request(LM_STUDIO_URL, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"LLM Error: {e}")
    return None

def generate_heuristic(base_code):
    prompt = f"""
§BOOT\\[prime] :=
  stance := AutoModSAT Coder
  density := high, python
  operator := §MUTATE
§EMIT_1 : Improve the following choose_heuristic function to map CNFProfile to Kissat Heuristic.
Use the features in CNFProfile (num_vars, num_clauses, horn_ratio, max_clause_len) to intelligently select between AGGRESSIVE and CONSERVATIVE.
Provide ONLY the python code for `def choose_heuristic(profile: CNFProfile) -> Heuristic:`

Original Code:
{base_code}

§RESONATE
§ABSORB
"""
    return query_llm(prompt, temperature=0.7)

def run_evolution(iterations=5):
    print("§[EVOLUTION] Initializing Active Learning Oracle...")
    data = load_dataset('../docs/ladder/scripts/benchmark_206_results.json')
    al_sample = active_learning_sample(data, sample_size=20)
    print(f"§[EVOLUTION] Sampled {len(al_sample)} instances for fast evaluation.")
    
    base_code = """
def choose_heuristic(profile: CNFProfile) -> Heuristic:
    del profile
    return AGGRESSIVE
"""
    
    best_par2 = float('inf')
    best_code = base_code
    
    for i in range(iterations):
        print(f"\\n§[EVOLUTION] Iteration {i+1}/{iterations}...")
        
        # 1. Coder
        new_code = generate_heuristic(best_code)
        if not new_code:
            continue
            
        print("§[EVOLUTION] Generated new heuristic. Evaluating...")
        
        # 2. Evaluate
        par2 = evaluate_heuristic_on_sample(new_code, al_sample)
        print(f"§[EVOLUTION] Predicted PAR-2: {par2:.2f} (Best: {best_par2:.2f})")
        
        if par2 < best_par2:
            print("§[EVOLUTION] Improved! Retaining new heuristic.")
            best_par2 = par2
            best_code = new_code
            
    print("\\n§[EVOLUTION] Evolution complete. Best PAR-2:", best_par2)
    print("Best Code:\\n", best_code)

if __name__ == '__main__':
    run_evolution(iterations=3)
