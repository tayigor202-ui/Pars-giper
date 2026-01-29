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
        data = json.loads(sys.argv[1])
        skus = data.get('skus', [])
        region_ids = data.get('region_ids', [1])
        
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
            
            # Get URLs for requested SKUs
            sku_tuples = tuple(str(s) for s in skus)
            if not sku_tuples:
                 db_urls = {}
            else:
                # Handle single item tuple syntax (x,)
                if len(sku_tuples) == 1:
                    query = "SELECT sku, url FROM lemana_prices WHERE sku = %s"
                    cur.execute(query, (sku_tuples[0],))
                else:
                    query = "SELECT sku, url FROM lemana_prices WHERE sku IN %s"
                    cur.execute(query, (sku_tuples,))
                
                db_urls = {row[0]: row[1] for row in cur.fetchall()}
            
            cur.close()
            conn.close()
        except Exception as db_err:
            print(f"[TARGETED] Warning: Could not fetch URLs from DB: {db_err}")
            db_urls = {}

        # Format for run_lemana_parsing
        # Use URL from DB if available, otherwise just SKU (which will fallback to short URL)
        skus_list = []
        for sku in skus:
            url = db_urls.get(str(sku))
            if url:
                print(f"[TARGETED] Using DB URL for {sku}: {url}")
            else:
                print(f"[TARGETED] No DB URL for {sku}, using default.")
                
            skus_list.append({
                "sku": sku, 
                "competitor": "Lemana Pro",
                "url": url
            })
        
        print(f"[TARGETED] Starting parsing for {len(skus)} SKUs in {len(region_ids)} regions...")
        run_lemana_parsing(skus_list, region_ids=region_ids)
        print("[TARGETED] All tasks completed.")
        
    except Exception as e:
        print(f"[TARGETED] Error: {e}")

if __name__ == "__main__":
    main()
