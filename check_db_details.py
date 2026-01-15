import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def check_db():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # Check all unique competitor names with counts
    cur.execute("""
        SELECT competitor_name, COUNT(*) as count 
        FROM public.prices 
        GROUP BY competitor_name 
        ORDER BY count DESC
    """)
    
    print("Competitor names in database:")
    for name, count in cur.fetchall():
        print(f"  {name}: {count} rows")
    
    print("\n" + "="*50)
    
    # Check for NULL competitor_name
    cur.execute("SELECT COUNT(*) FROM public.prices WHERE competitor_name IS NULL")
    null_count = cur.fetchone()[0]
    print(f"Rows with NULL competitor_name: {null_count}")
    
    # Sample rows with invalid names
    cur.execute("""
        SELECT sku, competitor_name, status, name 
        FROM public.prices 
        WHERE competitor_name NOT IN ('Ссылка на наш магазин', 'Магазин DeLonghi Group', 'Delonghi official store')
        LIMIT 10
    """)
    
    print("\nSample invalid rows:")
    for row in cur.fetchall():
        print(f"  SKU: {row[0]}, Competitor: {row[1]}, Status: {row[2]}, Name: {row[3][:50] if row[3] else 'None'}...")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_db()
