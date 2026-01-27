"""Check database connection with different credentials"""
import psycopg2

print("\nChecking PostgreSQL connection...")
print("="*60)

# Try different common passwords
passwords_to_try = ['postgres', 'admin', '1234', 'password', '']

for pwd in passwords_to_try:
    try:
        print(f"\nTrying password: '{'***' if pwd else '(empty)'}'")
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password=pwd,
            database='postgres'
        )
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        print(f"SUCCESS! Connected to PostgreSQL")
        print(f"Version: {version[:50]}...")
        
        # Check if ozon_parser database exists
        cur.execute("SELECT datname FROM pg_database WHERE datname='ozon_parser'")
        db_exists = cur.fetchone()
        
        if db_exists:
            print("Database 'ozon_parser' EXISTS")
        else:
            print("Database 'ozon_parser' DOES NOT EXIST")
            print("Creating database...")
            conn.autocommit = True
            cur.execute("CREATE DATABASE ozon_parser")
            print("Database 'ozon_parser' CREATED")
        
        cur.close()
        conn.close()
        
        # Update .env with correct password
        print(f"\nUpdating .env file with correct password...")
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace password line
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if line.startswith('DB_PASS='):
                new_lines.append(f'DB_PASS={pwd}')
            else:
                new_lines.append(line)
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        print("Updated .env file")
        print("="*60)
        break
        
    except psycopg2.OperationalError as e:
        if 'password authentication failed' in str(e):
            print(f"FAILED: Wrong password")
        else:
            print(f"FAILED: {e}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\nCould not connect to PostgreSQL with any common password")
    print("Please check PostgreSQL installation and credentials")
