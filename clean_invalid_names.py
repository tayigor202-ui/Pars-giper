import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

def clean_database():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Valid competitor names from Google Sheet
        valid_names = [
            'Ссылка на наш магазин',
            'Магазин DeLonghi Group',
            'Delonghi official store',
            'Delonghi официальный магазин',
            'Kenwood официальный магазин',
            'Braun официальный магазин'
        ]
        
        # Delete rows where competitor_name is NOT in the valid list
        # We use a parameterized query with ANY for safety
        query = "DELETE FROM public.prices WHERE competitor_name != ALL(%s)"
        cur.execute(query, (valid_names,))
        deleted_count = cur.rowcount
        
        conn.commit()
        print(f"Deleted {deleted_count} rows with invalid competitor names.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clean_database()
