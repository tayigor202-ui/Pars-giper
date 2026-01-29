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
from wb_silent_parser import run_wb_silent_parsing, cleanup_resources
from wb_reporting import generate_wb_report, send_wb_report # New import

load_dotenv()

def main():
    print("="*70)
    print(" WILDBERRIES PRODUCTION PARSER (SILENT API ENGINE) ")
    print("="*70)
    if os.name == 'nt':
        os.system('title WB Parser (Full)')
    
    # Clean up old reports before starting
    print("[CLEANUP] Removing old WB report files...")
    try:
        import glob
        for old_report in glob.glob("wb_prices_report_*.xlsx"):
            try:
                os.remove(old_report)
                print(f"[CLEANUP] 🗑️ Deleted: {old_report}")
            except:
                pass
    except Exception as e:
        print(f"[CLEANUP] ⚠️ Could not clean old reports: {e}")
    
    try:
        run_wb_silent_parsing()
        
        # Report generation
        print("\n" + "="*70)
        report_file = generate_wb_report()
        if report_file:
            send_wb_report(report_file)
            
    except KeyboardInterrupt:
        print("\n[STOP] Parsing interrupted by user.")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup_resources()

if __name__ == "__main__":
    main()
