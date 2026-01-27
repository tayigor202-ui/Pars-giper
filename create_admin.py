import psycopg2
import bcrypt

print("Creating admin user...")

# Try different passwords
for pwd in ['postgres', 'admin', '1234', 'root']:
    try:
        conn = psycopg2.connect(
            host='127.0.0.1',
            port=5432,
            user='postgres',
            password=pwd,
            database='ozon_parser',
            options='-c client_encoding=UTF8'
        )
        
        print(f"Connected! Password works: ***")
        cur = conn.cursor()
        
        # Create table if not exists
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
        
        # Check if admin exists
        cur.execute("SELECT id FROM public.users WHERE username='admin'")
        if cur.fetchone():
            print("Admin exists. Resetting password...")
            hash = bcrypt.hashpw(b'admin', bcrypt.gensalt()).decode('utf-8')
            cur.execute("UPDATE public.users SET password_hash=%s WHERE username='admin'", (hash,))
        else:
            print("Creating admin...")
            hash = bcrypt.hashpw(b'admin', bcrypt.gensalt()).decode('utf-8')
            cur.execute("""
                INSERT INTO public.users (
                    username, password_hash, full_name,
                    can_view_dashboard, can_run_parser, can_view_parser_status,
                    can_view_settings, can_edit_schedules, can_edit_database_settings,
                    can_import_data, can_manage_users
                ) VALUES (
                    'admin', %s, 'Administrator',
                    TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE
                )
            """, (hash,))
        
        conn.commit()
        
        # Show users
        cur.execute("SELECT username, full_name FROM public.users WHERE is_active=TRUE")
        print("\nUsers:")
        for u in cur.fetchall():
            print(f"  - {u[0]} ({u[1]})")
        
        cur.close()
        conn.close()
        
        print("\nSUCCESS!")
        print("Login: admin")
        print("Password: admin")
        print("URL: http://localhost:3454")
        break
        
    except psycopg2.OperationalError as e:
        if 'does not exist' in str(e):
            print(f"Database does not exist. Creating...")
            try:
                c = psycopg2.connect(host='127.0.0.1', port=5432, user='postgres', password=pwd, database='postgres', options='-c client_encoding=UTF8')
                c.autocommit = True
                c.cursor().execute("CREATE DATABASE ozon_parser")
                c.close()
                print("Database created! Run again.")
            except:
                pass
            break
        continue
    except Exception as e:
        print(f"Error: {e}")
        break
