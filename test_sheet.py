import pandas as pd
import requests
import io

URL = "https://docs.google.com/spreadsheets/d/1yYpnpS0HkybD-Xsc5iPhlbPKC0r8yp3oG-HMDIVluvw/export?format=csv"

def test():
    try:
        r = requests.get(URL)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.text))
            print(f"Columns: {list(df.columns)}")
            print(f"Rows: {len(df)}")
            print("\nFirst 5 rows:")
            print(df.head(5))
        else:
            print(f"Error fetching: {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
