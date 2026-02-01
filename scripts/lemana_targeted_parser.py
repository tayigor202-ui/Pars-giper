import os
import sys
import json
import threading

# Add parent and parsers dir to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, 'parsers'))

from lemana_silent_parser import run_lemana_parsing

def main():
    if len(sys.argv) < 2:
        print("Usage: python lemana_targeted_parser.py '<json_data>'")
        return

    if os.name == 'nt':
        os.system('title Lemana Pro Parser (Targeted)')

    try:
        # Try to parse as JSON first (from dashboard)
        if sys.argv[1].startswith('{'):
            data = json.loads(sys.argv[1])
            skus = data.get('skus', [])
            region_ids = data.get('region_ids', [1])
        else:
            # Simple CLI arguments: SKU [RegionID] [Platform]
            skus = [sys.argv[1]]
            region_ids = [34]
            if len(sys.argv) > 2:
                region_ids = [int(sys.argv[2])]
        
        conn = None
        try:
            import psycopg2
            from dotenv import load_dotenv
            load_dotenv()
            
            # Fetch URLs from DB to ensure we parse the correct link
            conn = psycopg2.connect(
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASS'),
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT')
            )
            cur = conn.cursor()
            
            # Get URLs and RIC prices for requested SKUs
            sku_tuples = tuple(str(s) for s in skus)
            if not sku_tuples:
                 db_data = {}
            else:
                if len(sku_tuples) == 1:
                    query = "SELECT sku, url, ric_leroy_price FROM public.lemana_prices WHERE sku = %s AND competitor_name = 'Lemana Pro' ORDER BY ric_leroy_price ASC NULLS FIRST"
                    cur.execute(query, (sku_tuples[0],))
                else:
                    query = "SELECT sku, url, ric_leroy_price FROM public.lemana_prices WHERE sku IN %s AND competitor_name = 'Lemana Pro' ORDER BY sku, ric_leroy_price ASC NULLS FIRST"
                    cur.execute(query, (sku_tuples,))
                
                db_data = {row[0]: {"url": row[1], "ric": row[2]} for row in cur.fetchall()}
            
            cur.close()
            conn.close()
        except Exception as db_err:
            print(f"[TARGETED] Warning: Could not fetch URLs from DB: {db_err}")
            db_data = {}

        # Format for run_lemana_parsing
        skus_list = []
        for sku in skus:
            info = db_data.get(str(sku), {})
            url = info.get('url')
            ric = info.get('ric')
            
            if url:
                print(f"[TARGETED] Using DB URL for {sku}: {url} (RIC: {ric})")
            else:
                print(f"[TARGETED] No DB URL for {sku}, using default.")
                
            skus_list.append({
                "sku": sku, 
                "competitor": "Lemana Pro",
                "url": url,
                "ric_leroy_price": ric
            })
        
        print(f"[TARGETED] Starting parsing for {len(skus)} SKUs in {len(region_ids)} regions...")
        run_lemana_parsing(skus_list, region_ids=region_ids)
        print("[TARGETED] All tasks completed.")
        
    except Exception as e:
        print(f"[TARGETED] Error: {e}")

if __name__ == "__main__":
    main()
