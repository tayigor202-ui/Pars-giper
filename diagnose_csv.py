import pandas as pd
import requests
import io

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1yYpnpS0HkybD-Xsc5iPhlbPKC0r8yp3oG-HMDIVluvw/export?format=csv"

print("="*60)
print("DIAGNOSTIC: GOOGLE SHEETS CSV EXPORT")
print("="*60)
try:
    print(f"Fetching URL: {SPREADSHEET_URL}")
    response = requests.get(SPREADSHEET_URL)
    response.encoding = 'utf-8'
    content = response.text
    
    print("\n[RAW CONTENT SAMPLE (First 500 chars)]:")
    print(content[:500])
    
    # Parse CSV
    df = pd.read_csv(io.StringIO(content))
    print("\n"+"="*60)
    print(f"COLUMNS FOUND ({len(df.columns)}):")
    for i, col in enumerate(df.columns):
        print(f"{i+1}. {col}")
    print("="*60)
    
    print(f"\nTOTAL ROWS: {len(df)}")
    
    competitors = [c for c in df.columns if 'сп-код' not in c.lower() and 'спкод' not in c.lower() and 'sp-kod' not in c.lower() and 'наименование' not in c.lower() and 'название' not in c.lower() and 'name' not in c.lower()]
    print(f"\nDETECTED COMPETITOR COLUMNS ({len(competitors)}):")
    for c in competitors:
        print(f" - {c}")

except Exception as e:
    print(f"ERROR: {e}")
