
import os
import psycopg2
from dotenv import load_dotenv

def fix_mangled_string(s):
    if not s:
        return s
    
    # Common patterns of Mojibake from UTF-8 -> Latin-1/CP1252
    try:
        # Try encoding back to bytes using CP1252 (common on Windows) and decoding as UTF-8
        fixed = s.encode('cp1252').decode('utf-8')
        if fixed != s:
            return fixed
    except:
        try:
            # Fallback to latin-1
            fixed = s.encode('latin-1').decode('utf-8')
            if fixed != s:
                return fixed
        except:
            pass
            
    return s

def main():
    load_dotenv()
    
    db_params = {
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASS'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT')
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        
        print("[FIX] Searching for mangled names in lemana_prices...")
        
        # We look for names containing common Mojibake starter characters for Cyrillic
        # Ð is \xd0, which starts almost all Russian characters in UTF-8
        cur.execute("SELECT sku, region_id, name FROM public.lemana_prices WHERE name LIKE '%Ð%' OR name LIKE '%â%'")
        rows = cur.fetchall()
        
        print(f"[FIX] Found {len(rows)} potentially mangled names.")
        
        updated_count = 0
        for sku, rid, name in rows:
            fixed_name = fix_mangled_string(name)
            if fixed_name != name:
                cur.execute(
                    "UPDATE public.lemana_prices SET name = %s WHERE sku = %s AND region_id = %s AND competitor_name = 'Lemana Pro'",
                    (fixed_name, sku, rid)
                )
                updated_count += 1
                if updated_count % 100 == 0:
                    print(f"[FIX] Progress: {updated_count}/{len(rows)} fixed...")
        
        conn.commit()
        print(f"[FIX] Successfully updated {updated_count} names.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[FIX] Error: {e}")

if __name__ == "__main__":
    main()
