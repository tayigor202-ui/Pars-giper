"""
User Management Module
Handles user CRUD operations, authentication, and permissions
"""
import os
import psycopg2
import bcrypt
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Database connection
DB_URL = os.getenv('DB_URL')
if not DB_URL:
    DB_USER = os.getenv('DB_USER', 'GiperBox')
    DB_PASS = os.getenv('DB_PASS', 'Gingerik83')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'ParserOzon')
    DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

class UserManager:
    """User management operations"""
    
    @staticmethod
    def hash_password(password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password, password_hash):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def get_user_by_username(username):
        """Get user by username"""
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, username, password_hash, full_name, email, 
                   created_at, last_login, is_active,
                   can_view_dashboard, can_run_parser, can_view_parser_status,
                   can_view_settings, can_edit_schedules, can_edit_database_settings,
                   can_import_data, can_manage_users
            FROM public.users 
            WHERE username = %s AND is_active = TRUE
        """, (username,))
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            return None
            
        return {
            'id': row[0],
            'username': row[1],
            'password_hash': row[2],
            'full_name': row[3],
            'email': row[4],
            'created_at': row[5],
            'last_login': row[6],
            'is_active': row[7],
            'permissions': {
                'can_view_dashboard': row[8],
                'can_run_parser': row[9],
                'can_view_parser_status': row[10],
                'can_view_settings': row[11],
                'can_edit_schedules': row[12],
                'can_edit_database_settings': row[13],
                'can_import_data': row[14],
                'can_manage_users': row[15]
            }
        }
    
    @staticmethod
    def get_all_users():
        """Get all users"""
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, username, full_name, email, created_at, last_login, is_active,
                   can_view_dashboard, can_run_parser, can_view_parser_status,
                   can_view_settings, can_edit_schedules, can_edit_database_settings,
                   can_import_data, can_manage_users
            FROM public.users 
            ORDER BY created_at DESC
        """)
        
        users = []
        for row in cur.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'full_name': row[2],
                'email': row[3],
                'created_at': row[4].isoformat() if row[4] else None,
                'last_login': row[5].isoformat() if row[5] else None,
                'is_active': row[6],
                'permissions': {
                    'can_view_dashboard': row[7],
                    'can_run_parser': row[8],
                    'can_view_parser_status': row[9],
                    'can_view_settings': row[10],
                    'can_edit_schedules': row[11],
                    'can_edit_database_settings': row[12],
                    'can_import_data': row[13],
                    'can_manage_users': row[14]
                }
            })
        
        cur.close()
        conn.close()
        return users
    
    @staticmethod
    def create_user(username, password, full_name='', email='', permissions=None):
        """Create new user"""
        if permissions is None:
            permissions = {
                'can_view_dashboard': True,
                'can_run_parser': False,
                'can_view_parser_status': True,
                'can_view_settings': False,
                'can_edit_schedules': False,
                'can_edit_database_settings': False,
                'can_import_data': False,
                'can_manage_users': False
            }
        
        password_hash = UserManager.hash_password(password)
        
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO public.users (
                    username, password_hash, full_name, email,
                    can_view_dashboard, can_run_parser, can_view_parser_status,
                    can_view_settings, can_edit_schedules, can_edit_database_settings,
                    can_import_data, can_manage_users
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                username, password_hash, full_name, email,
                permissions.get('can_view_dashboard', True),
                permissions.get('can_run_parser', False),
                permissions.get('can_view_parser_status', True),
                permissions.get('can_view_settings', False),
                permissions.get('can_edit_schedules', False),
                permissions.get('can_edit_database_settings', False),
                permissions.get('can_import_data', False),
                permissions.get('can_manage_users', False)
            ))
            
            user_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            return user_id
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            cur.close()
            conn.close()
            raise ValueError(f"User '{username}' already exists")
    
    @staticmethod
    def update_user(user_id, data):
        """Update user data and permissions"""
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Build dynamic UPDATE query
        update_fields = []
        update_values = []
        
        if 'full_name' in data:
            update_fields.append('full_name = %s')
            update_values.append(data['full_name'])
        
        if 'email' in data:
            update_fields.append('email = %s')
            update_values.append(data['email'])
        
        if 'is_active' in data:
            update_fields.append('is_active = %s')
            update_values.append(data['is_active'])
        
        if 'password' in data and data['password']:
            update_fields.append('password_hash = %s')
            update_values.append(UserManager.hash_password(data['password']))
        
        # Update permissions
        if 'permissions' in data:
            for perm, value in data['permissions'].items():
                update_fields.append(f'{perm} = %s')
                update_values.append(value)
        
        if not update_fields:
            cur.close()
            conn.close()
            return
        
        update_values.append(user_id)
        query = f"UPDATE public.users SET {', '.join(update_fields)} WHERE id = %s"
        
        cur.execute(query, update_values)
        conn.commit()
        cur.close()
        conn.close()
    
    @staticmethod
    def delete_user(user_id):
        """Delete user (or mark as inactive)"""
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Soft delete - just mark as inactive
        cur.execute("UPDATE public.users SET is_active = FALSE WHERE id = %s", (user_id,))
        
        conn.commit()
        cur.close()
        conn.close()
    
    @staticmethod
    def update_last_login(user_id):
        """Update last login timestamp"""
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        cur.execute("UPDATE public.users SET last_login = NOW() WHERE id = %s", (user_id,))
        
        conn.commit()
        cur.close()
        conn.close()
