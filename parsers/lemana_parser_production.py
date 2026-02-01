import os, sys, time, random, io

# Add project root and scripts directory to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
SCRIPTS_DIR = os.path.join(ROOT_DIR, 'scripts')
if SCRIPTS_DIR not in sys.path:
    sys.path.append(SCRIPTS_DIR)

# Force UTF-8 encoding for stdout and stderr to handle emojis and Russian text
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
import psycopg2
from lemana_silent_parser import run_lemana_parsing
from lemana_reporting import generate_lemana_report, send_lemana_report
from core.lemana_utils import LEMANA_ALL_REGION_IDS

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def main():
    print("="*70)
    print(" LEMANA PRO PRODUCTION PARSER ")
    print("="*70)
    if os.name == 'nt':
        os.system('title Lemana Pro Parser (Full)')
    
    # Clean up old reports before starting
    print("[CLEANUP] Removing old Lemana report files...")
    try:
        import glob
        for old_report in glob.glob("lemana_prices_report_*.xlsx"):
            try:
                os.remove(old_report)
                print(f"[CLEANUP] 🗑️ Deleted: {old_report}")
            except:
                pass
    except Exception as e:
        print(f"[CLEANUP] ⚠️ Could not clean old reports: {e}")
    
    try:
        # Load tasks from DB
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        # Use DISTINCT ON (sku) to avoid redundant tasks. 
        # Ordering by url DESC NULLS LAST ensures we pick an entry that already has a full URL if available.
        cur.execute("""
            SELECT DISTINCT ON (sku) sku, competitor_name, sp_code, url, ric_leroy_price 
            FROM public.lemana_prices 
            WHERE sku IS NOT NULL
            ORDER BY sku, ric_leroy_price DESC NULLS LAST, url DESC NULLS LAST
        """)
        items = cur.fetchall()
        cur.close()
        conn.close()
        
        if not items:
            print("[INFO] No items to parse for Lemana Pro.")
            return

        print(f"[INFO] Found {len(items)} items to parse.")
        
        # Convert to list of dicts for the engine
        skus_list = [
            {"sku": i[0], "competitor": i[1], "sp_code": i[2], "url": i[3], "ric_leroy_price": i[4]} 
            for i in items
        ]
        
        # Run parsing
        run_lemana_parsing(skus_list, region_ids=LEMANA_ALL_REGION_IDS)
        
        # Report generation
        print("\n" + "="*70)
        report_file = generate_lemana_report()
        if report_file:
            print(f"[SUCCESS] Report generated: {report_file}")
            send_lemana_report(report_file)
            
    except KeyboardInterrupt:
        print("\n[STOP] Parsing interrupted by user.")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup browser processes robustly
        from core.lemana_utils import kill_lemana_browsers
        kill_lemana_browsers()

if __name__ == "__main__":
    main()
