import os
import csv
import urllib.request
import concurrent.futures as cf
import lzma
import shutil

def fetch_instances():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    benchmarks_dir = os.path.join(base_dir, 'real_2026_benchmarks')
    os.makedirs(benchmarks_dir, exist_ok=True)
    
    # 1. Download the selected_benchmarks.csv directly from the SAT 2026 GitHub
    csv_url = "https://raw.githubusercontent.com/satcompetition/2026/main/downloads/benchmark-compilation-script/selected_benchmarks.csv"
    csv_path = os.path.join(benchmarks_dir, "selected_benchmarks.csv")
    
    if not os.path.exists(csv_path):
        print(f"Downloading 2026 benchmark list...")
        urllib.request.urlretrieve(csv_url, csv_path)
    
    # 2. Read the hashes and families
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            
    print(f"Loaded {len(rows)} instances from SAT 2026 selected_benchmarks.csv")
    
    # 3. We want a sizable chunk (up to 500) of tractable instances for a full-scale test.
    # To protect disk space, we will cap the download size at 50MB per compressed instance.
    selected = []
    
    # We will try to get the sizes via a quick HEAD request, but to save time, we will just download
    # and skip if the Content-Length is too large.
    print(f"Selecting a massive chunk of up to 500 instances...")
    
    # Just take up to 500 instances from the CSV
    for r in rows[:500]:
        selected.append(r)
                
    print(f"Selected {len(selected)} candidate instances for downloading.")
    
    # 4. Download and decompress
    def download_and_extract(r):
        h = r['hash']
        fam = r['family']
        out_xz = os.path.join(benchmarks_dir, f"{fam}_{h[:8]}.cnf.xz")
        out_cnf = os.path.join(benchmarks_dir, f"{fam}_{h[:8]}.cnf")
        
        if os.path.exists(out_cnf):
            return f"Cached: {out_cnf}"
            
        try:
            url = f"https://benchmark-database.de/file/{h}"
            req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    content_length = int(response.headers.get('Content-Length', 0))
                    if content_length > 50 * 1024 * 1024:
                        return f"Skipped {h} (Too Large: {content_length // 1024 // 1024}MB)"
            except:
                pass # Proceed anyway if HEAD fails

            # Download xz
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as response, open(out_xz, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
                
            # Extract
            with lzma.open(out_xz, 'rb') as f_in, open(out_cnf, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
                
            # Clean up xz
            os.remove(out_xz)
            return f"Downloaded & Extracted: {out_cnf}"
        except Exception as e:
            return f"Failed {h}: {e}"
            
    with cf.ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(download_and_extract, selected))
        
    for res in results:
        print(res)
        
    print(f"Successfully populated {benchmarks_dir} with Real 2026 instances.")

if __name__ == "__main__":
    fetch_instances()
