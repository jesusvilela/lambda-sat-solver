import json
import urllib.request
import urllib.error
import concurrent.futures
import sys
import os

LM_STUDIO_URL = "http://192.168.56.1:1234/v1/chat/completions"
MODEL = "google/gemma-4-12b"

def map_breathing_space(instance_data):
    """
    Query Gemma to map the geometric breathing space of the solver traverse using urllib.
    """
    family = instance_data.get('family', 'unknown')
    # Get ID from data
    instance_id = instance_data.get('instance', instance_data.get('name', 'node'))
    
    # Safe traverse to mw time
    times = instance_data.get('times', {})
    mw_time = times.get('mw', '0.00')
    
    prompt = (
        f"§BOOT\\[prime] :=\n"
        f"  stance := Hegelian mutual-recognition\n"
        f"  density := high, geometric\n"
        f"  operator := §HOLOPORT\n"
        f"§EMIT_1 : {family} {instance_id} L_0={mw_time}s\n"
        f"§RESONATE : map breathing space and geometric traverse\n"
        f"§ABSORB\n"
    )
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "§-LANG v5.0 Interpreter (Trasgo Operational Layer)."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 2048
    }
    
    req = urllib.request.Request(LM_STUDIO_URL, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))
                content = result['choices'][0]['message']['content']
                return f"[§{family.upper()}::{instance_id}] Gemma Mapping:\n{content.strip()}"
            else:
                return f"[§{family.upper()}::{instance_id}] Error: HTTP {response.status}"
    except Exception as e:
        return f"[§{family.upper()}::{instance_id}] Exception: {repr(e)}"

def main():
    print(f"§[FLEET_ORCHESTRATOR] Booting Agent Fleet... Target LM: {MODEL}")
    
    try:
        with open('../docs/ladder/scripts/benchmark_206_results.json', 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading benchmark: {e}")
        return

    # Active Learning Sampling: Select 1 from each family to map the space
    families_seen = set()
    sampled_instances = []
    
    for row in data:
        family = row.get('family', 'mixed')
        if family not in families_seen:
            families_seen.add(family)
            sampled_instances.append(row)
            
    print(f"§[FLEET_ORCHESTRATOR] Active Learning Sample: Selected {len(sampled_instances)} topological extremes.")
    print("§[FLEET_ORCHESTRATOR] Launching threaded LM Studio telemetry bridge...")

    results = []
    print("§[FLEET_ORCHESTRATOR] Querying instances sequentially to prevent LM Studio context queuing...")
    for i, inst in enumerate(sampled_instances):
        print(f"§[FLEET_ORCHESTRATOR] Polling LM Studio for node {i+1}/{len(sampled_instances)}...")
        # Override timeout locally in the request function by passing it or just rely on the 45s but we need more
        # Wait, the timeout is hardcoded inside map_breathing_space. Let me just change the loop.
        res = map_breathing_space(inst)
        results.append(res)
        print(res)
        
    print("\n" + "="*50)
    print("=== GEOMETRIC BREATHING SPACE MAP ===")
    print("="*50)
    for r in results:
        print(r + "\n" + "-"*50)
        
    # Write output to an artifact file
    artifact_path = os.path.join(r"C:\\Users\\HAL900\\.gemini\\antigravity\\brain\\65b7ce14-0c42-4c8a-abb0-5568fc445a19", "breathing_space_report.md")
    with open(artifact_path, 'w', encoding='utf-8') as f:
        f.write("# Geometric Breathing Space Map\n\n")
        f.write("Generated via `google/gemma-4-12b` on LM Studio orchestrating the active learning sample traverse.\n\n")
        for r in results:
            f.write("```text\n" + r + "\n```\n\n")
            
    print(f"§[FLEET_ORCHESTRATOR] Report saved to artifact: breathing_space_report.md")

if __name__ == '__main__':
    main()
