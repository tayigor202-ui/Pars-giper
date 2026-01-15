
import ozon_parser_production_final as parser
import pandas as pd
import os

print("--- TESTING REPORT LAYOUT ---")
try:
    filename = parser.generate_excel_report()
    if filename:
        print(f"Report generated: {filename}")
        # Verify columns using pandas
        df = pd.read_excel(filename, sheet_name='Цены', header=[0,1])
        print("Columns found:")
        print(df.columns)
        
        # Check if SKU is present in secondary level
        levels = df.columns.levels
        if 'SKU' in levels[1]:
            print("SUCCESS: 'SKU' column exists for competitors.")
        else:
            print("FAILURE: 'SKU' column MISSING.")
            
    else:
        print("Report generation returned None")
except Exception as e:
    print(f"Error: {e}")
print("--- END TEST ---")
