"""
Direct database setup without .env file issues
Creates database and admin user
"""
import psycopg2
import bcrypt

print("\n" + "="*70)
print("DIRECT DATABASE SETUP")
print("="*70)

# Try to connect using common setups
connection_attempts = [
    {'host': 'localhost', 'port': 5432, 'user': 'postgres', 'password': 'postgres'},
    {'host': '127.0.0.1', 'port': 5432, 'user': 'postgres', 'password': 'postgres'},
    {'host': 'localhost', 'port': 5432, 'user': 'postgres', 'password': 'admin'},
    {'host': 'localhost', 'port': 5432, 'user': 'postgres', 'password': '1234'},
]

conn_params = None

print("\n1. Testing PostgreSQL connection...")
for params in connection_attempts:
    try:
        print(f"   Trying {params['host']}:{params['port']}...", end='')
        conn = psycopg2.connect(database='postgres', **params)
        conn.close()
        conn_params = params
        print(" SUCCESS!")
        break
    except Exception as e:
        print(f" Failed ({str(e)[:30]})")

if not conn_params:
    print("\nERROR: Could not connect to PostgreSQL with common credentials")
    if os.environ.get('NON_INTERACTIVE'):
        print("NON_INTERACTIVE mode: using 'postgres' as fallback password")
        conn_params = {'host': 'localhost', 'port': 5432, 'user': 'postgres', 'password': 'postgres'}
    else:
        print("Please provide the correct password for postgres user:")
        password = input("Password: ")
        conn_params = {'host': 'localhost', 'port': 5432, 'user': 'postgres', 'password': password}

print(f"\nUsing connection: {conn_params['host']}:{conn_params['port']}")

# Create database if not exists
print("\n2. Creating database 'ozon_parser'...")
try:
    conn = psycopg2.connect(database='postgres', **conn_params)
    conn.autocommit = True
    cur = conn.cursor()
    
    # Check if database exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname='ozon_parser'")
    if cur.fetchone():
        print("   Database already exists")
    else:
        cur.execute("CREATE DATABASE ozon_parser")
        print("   Database created successfully")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"   ERROR: {e}")
    exit(1)

# Create users table
print("\n3. Creating users table...")
try:
    conn = psycopg2.connect(database='ozon_parser', **conn_params)
    cur = conn.cursor()
    
    # Create users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100),
            email VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            can_view_dashboard BOOLEAN DEFAULT TRUE,
            can_run_parser BOOLEAN DEFAULT FALSE,
            can_view_parser_status BOOLEAN DEFAULT TRUE,
            can_view_settings BOOLEAN DEFAULT FALSE,
            can_edit_schedules BOOLEAN DEFAULT FALSE,
            can_edit_database_settings BOOLEAN DEFAULT FALSE,
            can_import_data BOOLEAN DEFAULT FALSE,
            can_manage_users BOOLEAN DEFAULT FALSE
        )
    """)
    conn.commit()
    print("   Table created successfully")
    
    # Check if admin user exists
    cur.execute("SELECT id FROM public.users WHERE username='admin'")
    if cur.fetchone():
        print("\n4. Admin user already exists")
    else:
        print("\n4. Creating admin user...")
        # Hash password
        password_hash = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cur.execute("""
            INSERT INTO public.users (
                username, password_hash, full_name, email,
                can_view_dashboard, can_run_parser, can_view_parser_status,
                can_view_settings, can_edit_schedules, can_edit_database_settings,
                can_import_data, can_manage_users
            ) VALUES (
                %s, %s, %s, %s,
                TRUE, TRUE, TRUE,
                TRUE, TRUE, TRUE,
                TRUE, TRUE
            )
        """, ('admin', password_hash, 'Administrator', ''))
        conn.commit()
        print("   Admin user created successfully")
        print("   Username: admin")
        print("   Password: admin")
        print("   WARNING: Change password in production!")
    
    # Show all users
    print("\n5. Current users:")
    cur.execute("SELECT id, username, full_name, is_active FROM public.users")
    users = cur.fetchall()
    for user in users:
        status = "ACTIVE" if user[3] else "INACTIVE"
        print(f"   - ID:{user[0]} | {user[1]} ({user[2]}) | {status}")
    
    cur.close()
    conn.close()
    
    print("\n" + "="*70)
    print("SETUP COMPLETE!")
    print("You can now login to http://localhost:3454")
    print("Username: admin")
    print("Password: admin")
    print("="*70 + "\n")
    
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()
