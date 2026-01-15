"""
Initialize User Management System
Creates users table and default admin account
"""
import os
import psycopg2
from user_management import UserManager
from dotenv import load_dotenv

load_dotenv()

# Database connection
DB_URL = os.getenv('DB_URL')
if not DB_URL:
    DB_USER = os.getenv('DB_USER')
    DB_PASS = os.getenv('DB_PASS')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def init_users_table():
    """Create users table and default admin user"""
    
    print("[INIT] Initializing user management system...")
    
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # Read SQL schema file
    sql_file = os.path.join('database', 'create_users_table.sql')
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_commands = f.read()
    
    try:
        # Create table
        print("[INIT] Creating users table...")
        cur.execute(sql_commands.split('-- Insert default admin user')[0])
        conn.commit()
        print("[INIT] OK Users table created")
        
        # Check if admin exists
        cur.execute("SELECT id FROM public.users WHERE username = 'admin'")
        if cur.fetchone():
            print("[INIT] Admin user already exists")
        else:
            # Create admin user with proper bcrypt hash
            print("[INIT] Creating default admin user...")
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin')
            
            UserManager.create_user(
                username='admin',
                password=admin_password,
                full_name='Administrator',
                email='',
                permissions={
                    'can_view_dashboard': True,
                    'can_run_parser': True,
                    'can_view_parser_status': True,
                    'can_view_settings': True,
                    'can_edit_schedules': True,
                    'can_edit_database_settings': True,
                    'can_import_data': True,
                    'can_manage_users': True
                }
            )
            print(f"[INIT] OK Admin user created (username: admin, password: {admin_password})")
            print("[INIT] WARNING: Change default password in production!")
        
        cur.close()
        conn.close()
        
        print("\n[INIT] User management system initialized successfully!")
        print("[INIT] You can now login with username 'admin'")
        
    except Exception as e:
        print(f"[INIT] ERROR: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        cur.close()
        conn.close()

if __name__ == '__main__':
    init_users_table()
