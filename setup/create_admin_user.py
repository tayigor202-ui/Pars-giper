"""
Create admin user without config files (avoid encoding issues)
Uses direct connection parameters
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import psycopg2
import bcrypt

print("\nCREATING ADMIN USER")
print("="*60)

# Direct connection - NO config files
passwords_to_try = ['postgres', 'admin', '1234', 'password', 'root']

success = False
for pwd in passwords_to_try:
    try:
        # Connect with explicit parameters to avoid config file encoding issues
        conn = psycopg2.connect(
            host='127.0.0.1',
            port=5432,
            user='postgres',
            password=pwd,
            database='ozon_parser',
            options='-c client_encoding=UTF8'  # Force UTF-8
        )
        
        print(f"\nConnected successfully with password: ***")
        cur = conn.cursor()
        
        # Check users table
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema='public' AND table_name='users'
        """)
        
        if cur.fetchone()[0] == 0:
            print("Users table does not exist. Creating...")
            
            # Create table
            cur.execute("""
                CREATE TABLE public.users (
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
            print("Table created!")
        
        # Check if admin exists
        cur.execute("SELECT id FROM public.users WHERE username='admin'")
        admin_exists = cur.fetchone()
        
        if admin_exists:
            print("\nAdmin user already exists!")
            print("Resetting password to 'admin'...")
            
            # Update password
            password_hash = bcrypt.hashpw(b'admin', bcrypt.gensalt()).decode('utf-8')
            cur.execute("UPDATE public.users SET password_hash=%s WHERE username='admin'", (password_hash,))
            conn.commit()
            print("Password reset successfully!")
        else:
            print("\nCreating admin user...")
            
            # Create admin
            password_hash = bcrypt.hashpw(b'admin', bcrypt.gensalt()).decode('utf-8')
            cur.execute("""
                INSERT INTO public.users (
                    username, password_hash, full_name, email,
                    can_view_dashboard, can_run_parser, can_view_parser_status,
                    can_view_settings, can_edit_schedules, can_edit_database_settings,
                    can_import_data, can_manage_users
                ) VALUES (
                    'admin', %s, 'Administrator', '',
                    TRUE, TRUE, TRUE,
                    TRUE, TRUE, TRUE,
                    TRUE, TRUE
                )
            """, (password_hash,))
            conn.commit()
            print("Admin user created!")
        
        # Show all users
        print("\nCurrent users in database:")
        cur.execute("SELECT id, username, full_name, is_active FROM public.users")
        users = cur.fetchall()
        
        if users:
            for u in users:
                status = "ACTIVE" if u[3] else "INACTIVE"
                print(f"  - {u[1]} ({u[2]}) - {status}")
        else:
            print("  No users found!")
        
        cur.close()
        conn.close()
        
        print("\n" + "="*60)
        print("SUCCESS!")
        print("Login at: http://localhost:3454")
        print("Username: admin")
        print("Password: admin")
        print("="*60)
        
        success = True
        break
        
    except psycopg2.OperationalError as e:
        if 'password authentication failed' in str(e):
            continue
        elif 'database "ozon_parser" does not exist' in str(e):
            print(f"\nDatabase 'ozon_parser' does not exist!")
            print("Creating database...")
            try:
                conn2 = psycopg2.connect(
                    host='127.0.0.1',
                    port=5432,
                    user='postgres',
                    password=pwd,
                    database='postgres',
                    options='-c client_encoding=UTF8'
                )
                conn2.autocommit = True
                cur2 = conn2.cursor()
                cur2.execute("CREATE DATABASE ozon_parser")
                cur2.close()
                conn2.close()
                print("Database created! Run script again.")
            except Exception as e2:
                print(f"Error creating database: {e2}")
            break
        else:
            print(f"Connection error: {e}")
            break
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        break

if not success:
    print("\nFailed to create admin user")
    print("Please check PostgreSQL credentials")
