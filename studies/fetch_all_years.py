import os
import csv
import urllib.request
import concurrent.futures as cf
import lzma
import shutil

def fetch_year(year):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    benchmarks_dir = os.path.join(base_dir, f'real_{year}_benchmarks')
    os.makedirs(benchmarks_dir, exist_ok=True)
    
    # 2024, 2025, 2026 generally follow this path pattern for the benchmark selection
    csv_url = f"https://raw.githubusercontent.com/satcompetition/{year}/main/downloads/benchmark-compilation-script/selected_benchmarks.csv"
    csv_path = os.path.join(benchmarks_dir, "selected_benchmarks.csv")
    
    if not os.path.exists(csv_path):
        print(f"[{year}] Downloading benchmark list...")
        try:
            req = urllib.request.Request(csv_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response, open(csv_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        except Exception as e:
            print(f"[{year}] Could not fetch benchmark list: {e}")
            return
            
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            
    print(f"[{year}] Loaded {len(rows)} instances.")
    
    # Take up to 200 instances to be fast but sizable
    selected = rows[:200]
    print(f"[{year}] Selected {len(selected)} candidate instances.")
    
    def download_and_extract(r):
        h = r['hash'] if 'hash' in r else r.get('MD5', '')
        if not h:
            return f"[{year}] No hash found"
            
        fam = r['family'] if 'family' in r else 'unknown'
        out_xz = os.path.join(benchmarks_dir, f"{fam}_{h[:8]}.cnf.xz")
        out_cnf = os.path.join(benchmarks_dir, f"{fam}_{h[:8]}.cnf")
        
        if os.path.exists(out_cnf):
            return f"[{year}] Cached: {out_cnf}"
            
        try:
            url = f"https://benchmark-database.de/file/{h}"
            req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    content_length = int(response.headers.get('Content-Length', 0))
                    if content_length > 50 * 1024 * 1024:
                        return f"[{year}] Skipped {h} (Too Large)"
            except:
                pass 

            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as response, open(out_xz, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
                
            with lzma.open(out_xz, 'rb') as f_in, open(out_cnf, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
                
            os.remove(out_xz)
            return f"[{year}] Downloaded: {out_cnf}"
        except Exception as e:
            return f"[{year}] Failed {h}: {e}"
            
    with cf.ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(download_and_extract, selected))
        
    print(f"[{year}] Successfully processed.")

if __name__ == "__main__":
    for y in [2024, 2025, 2026]:
        fetch_year(y)
