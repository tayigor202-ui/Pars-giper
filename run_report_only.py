
import ozon_parser_production_final as parser
import time

print("--- STARTING REPORT GENERATION TEST ---")
try:
    filename = parser.generate_excel_report()
    if filename:
        print(f"SUCCESS: Report generated as {filename}")
    else:
        print("FAILURE: Report generation returned None")
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
print("--- END TEST ---")
