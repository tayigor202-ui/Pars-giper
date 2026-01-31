import os
import sys
import psycopg2
from datetime import datetime

# Add project root to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from parsers.ym_silent_parser import run_ym_parsing
from core.ym_utils import YM_ALL_REGION_IDS

def get_all_ym_skus():
    """Fetches all unique SKUs from ym_prices table."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT sku FROM ym_prices")
        skus = [{'sku': r[0]} for r in cur.fetchall()]
        cur.close()
        conn.close()
        return skus
    except Exception as e:
        print(f"[YM PROD] Error fetching SKUs: {e}")
        return []

def main():
    print(f"--- Yandex Market Production Parser Started at {datetime.now()} ---")
    
    skus = get_all_ym_skus()
    if not skus:
        print("[YM PROD] No SKUs found in database. Exiting.")
        return

    print(f"[YM PROD] Found {len(skus)} unique products to parse.")
    
    # Run parsing for all regions defined in ym_utils
    # Using a subset of regions for production by default if preferred, 
    # but here we use all regions from YM_ALL_REGION_IDS
    run_ym_parsing(
        skus_list=skus,
        region_ids=YM_ALL_REGION_IDS,
        max_workers=5,
        headless=True
    )
    
    print(f"--- Yandex Market Production Parser Finished at {datetime.now()} ---")

if __name__ == "__main__":
    main()
