import os
import json
import psycopg2
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import bcrypt
from dotenv import load_dotenv
import subprocess
import threading
import scheduler
from user_management import UserManager
from functools import wraps
import pandas as pd
import io

CONFIG_FILE = 'config.json'
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "ozon_spreadsheet_url": "",
        "wb_spreadsheet_url": ""
    }

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['id'])
        self.username = user_data['username']
        self.full_name = user_data.get('full_name', '')
        self.email = user_data.get('email', '')
        self.permissions = user_data.get('permissions', {})
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        return self.permissions.get(permission, False)

@login_manager.user_loader
def load_user(user_id):
    """Load user from database by ID"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'ParserOzon'),
            user=os.getenv('DB_USER', 'GiperBox'),
            password=os.getenv('DB_PASS', 'Gingerik83'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, full_name, email,
                   can_view_dashboard, can_run_parser, can_view_parser_status,
                   can_view_settings, can_edit_schedules, can_edit_database_settings,
                   can_import_data, can_manage_users
            FROM public.users WHERE id = %s AND is_active = TRUE
        """, (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            return None
        
        user_data = {
            'id': row[0],
            'username': row[1],
            'full_name': row[2],
            'email': row[3],
            'permissions': {
                'can_view_dashboard': row[4],
                'can_run_parser': row[5],
                'can_view_parser_status': row[6],
                'can_view_settings': row[7],
                'can_edit_schedules': row[8],
                'can_edit_database_settings': row[9],
                'can_import_data': row[10],
                'can_manage_users': row[11]
            }
        }
        return User(user_data)
    except:
        return None

# Permission decorators
def permission_required(permission):
    """Decorator to check if user has specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                # For API endpoints, return JSON error instead of redirect
                if request.path.startswith('/api/'):
                    return jsonify({'status': 'error', 'message': 'Требуется авторизация'}), 401
                return redirect(url_for('login'))
            if not current_user.has_permission(permission):
                # For API endpoints, return JSON error instead of redirect
                if request.path.startswith('/api/'):
                    return jsonify({'status': 'error', 'message': 'Недостаточно прав'}), 403
                flash('У вас нет доступа к этой функции', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Get user from database
        user_data = UserManager.get_user_by_username(username)
        
        if user_data and UserManager.verify_password(password, user_data['password_hash']):
            user = User(user_data)
            login_user(user, remember=True)
            
            # Update last login
            UserManager.update_last_login(user_data['id'])
            
            return redirect(url_for('dashboard'))
        else:
            flash('Неверные учётные данные', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
@permission_required('can_view_dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/parser')
@login_required
@permission_required('can_view_parser_status')
def parser():
    return render_template('parser_control.html')

@app.route('/settings')
@login_required
@permission_required('can_view_settings')
def settings():
    return render_template('settings.html')

@app.route('/api/parser/start', methods=['POST'])
@login_required
@permission_required('can_run_parser')
def start_parser():
    try:
        # Start run_all.bat in separate window with absolute path
        bat_file = os.path.join(ROOT_DIR, 'run_all.bat')
        # Improved command for Windows start - /c means close window after completion
        cmd = f'start "OZON Parser" cmd /c "{bat_file}"'
        subprocess.Popen(cmd, cwd=ROOT_DIR, shell=True)
        return jsonify({'status': 'success', 'message': 'Парсинг OZON запущен'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/git/pull', methods=['POST'])
@login_required
@permission_required('can_run_parser')
def git_pull():
    try:
        # Execute git pull
        output = subprocess.check_output(['git', 'pull', 'origin', 'main'], stderr=subprocess.STDOUT, text=True)
        return jsonify({'status': 'success', 'message': 'Обновление успешно!', 'output': output})
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'message': 'Ошибка Git Pull', 'output': e.output})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Системная ошибка: {str(e)}'})

@app.route('/api/parser/stop', methods=['POST'])
@login_required
@permission_required('can_run_parser')
def stop_parser():
    try:
        # Kill both Ozon and WB parser windows and processes
        subprocess.run(['taskkill', '/F', '/FI', 'WINDOWTITLE eq OZON Parser*', '/T'], shell=True)
        subprocess.run(['taskkill', '/F', '/FI', 'WINDOWTITLE eq WB Parser*', '/T'], shell=True)
        # Also kill any orphan python processes that might be running our parsers
        # This is a bit aggressive, but ensures everything stops
        return jsonify({'status': 'success', 'message': 'Все процессы парсинга остановлены'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/wb/parser/start', methods=['POST'])
@login_required
@permission_required('can_run_parser')
def start_wb_parser():
    try:
        # Start run_wb.bat in separate window with absolute path
        bat_file = os.path.join(ROOT_DIR, 'run_wb.bat')
        # Improved command for Windows start - /c means close window after completion
        cmd = f'start "WB Parser" cmd /c "{bat_file}"'
        subprocess.Popen(cmd, cwd=ROOT_DIR, shell=True)
        return jsonify({'status': 'success', 'message': 'Парсинг Wildberries запущен'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/database/update', methods=['POST'])
@login_required
@permission_required('can_import_data')
def update_database():
    try:
        config = load_config()
        url = request.json.get('url') if request.is_json else None
        
        # If no URL provided in request, use the one from config
        if not url:
            url = config.get('ozon_spreadsheet_url')
            
        cmd = ['python', 'import_from_sheets.py']
        if url: cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            return jsonify({'status': 'success', 'message': 'База OZON обновлена'})
        else:
            return jsonify({'status': 'error', 'message': f'Ошибка OZON: {result.stderr}'})
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'message': 'Превышено время ожидания OZON'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/database/update_wb', methods=['POST'])
@login_required
@permission_required('can_import_data')
def update_database_wb():
    try:
        config = load_config()
        url = request.json.get('url') if request.is_json else None
        
        # If no URL provided in request, use the one from config
        if not url:
            url = config.get('wb_spreadsheet_url')
            
        cmd = ['python', 'import_wb_from_sheets.py']
        if url: cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            return jsonify({'status': 'success', 'message': 'База Wildberries обновлена'})
        else:
            return jsonify({'status': 'error', 'message': f'Ошибка WB: {result.stderr}'})
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'message': 'Превышено время ожидания WB'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/config', methods=['GET'])
@login_required
@permission_required('can_view_settings')
def get_config_api():
    return jsonify(load_config())

@app.route('/api/config', methods=['POST'])
@login_required
@permission_required('can_edit_database_settings')
def save_config_api():
    try:
        new_config = request.json
        current_config = load_config()
        current_config.update(new_config)
        save_config(current_config)
        return jsonify({'status': 'success', 'message': 'Настройки сохранены'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# TEMPORARY: Force update endpoint without auth (REMOVE IN PRODUCTION!)
@app.route('/api/config/force_update', methods=['POST'])
def force_update_config_api():
    """TEMPORARY endpoint to update config without auth - for debugging only!"""
    try:
        new_config = request.json
        current_config = load_config()
        current_config.update(new_config)
        save_config(current_config)
        return jsonify({'status': 'success', 'message': 'Config updated (NO AUTH)', 'config': current_config})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Telegram Settings API
@app.route('/api/telegram/settings', methods=['GET'])
@login_required
@permission_required('can_view_settings')
def get_telegram_settings():
    """Get Telegram settings from .env"""
    try:
        return jsonify({
            'bot_token': os.getenv('TG_BOT_TOKEN', ''),
            'chat_id': os.getenv('TG_CHAT_ID', '')
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/telegram/settings', methods=['POST'])
@login_required
@permission_required('can_edit_database_settings')
def save_telegram_settings():
    """Save Telegram settings to .env file"""
    try:
        data = request.json
        bot_token = data.get('bot_token', '').strip()
        chat_id = data.get('chat_id', '').strip()
        
        if not bot_token or not chat_id:
            return jsonify({'status': 'error', 'message': 'Bot Token и Chat ID обязательны'}), 400
        
        # Read current .env file
        env_path = '.env'
        env_lines = []
        
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                env_lines = f.readlines()
        
        # Update or add TG_BOT_TOKEN and TG_CHAT_ID
        updated_bot_token = False
        updated_chat_id = False
        
        for i, line in enumerate(env_lines):
            if line.startswith('TG_BOT_TOKEN='):
                env_lines[i] = f'TG_BOT_TOKEN={bot_token}\n'
                updated_bot_token = True
            elif line.startswith('TG_CHAT_ID='):
                env_lines[i] = f'TG_CHAT_ID={chat_id}\n'
                updated_chat_id = True
        
        # Add if not found
        if not updated_bot_token:
            env_lines.append(f'TG_BOT_TOKEN={bot_token}\n')
        if not updated_chat_id:
            env_lines.append(f'TG_CHAT_ID={chat_id}\n')
        
        # Write back to .env
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(env_lines)
        
        # Reload environment variables
        load_dotenv(override=True)
        
        return jsonify({'status': 'success', 'message': 'Настройки Telegram сохранены в .env'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/telegram/test', methods=['POST'])
@login_required
@permission_required('can_view_settings')
def test_telegram_connection():
    """Test Telegram bot connection and send test message"""
    try:
        import requests
        
        data = request.json
        bot_token = data.get('bot_token', '').strip()
        chat_id = data.get('chat_id', '').strip()
        
        if not bot_token or not chat_id:
            return jsonify({'status': 'error', 'message': 'Bot Token и Chat ID обязательны'}), 400
        
        # Test 1: Check bot
        bot_url = f'https://api.telegram.org/bot{bot_token}/getMe'
        bot_response = requests.get(bot_url, timeout=10)
        
        if bot_response.status_code != 200:
            return jsonify({'status': 'error', 'message': f'Ошибка бота: HTTP {bot_response.status_code}'}), 400
        
        bot_result = bot_response.json()
        if not bot_result.get('ok'):
            return jsonify({'status': 'error', 'message': f'Неверный Bot Token: {bot_result.get("description", "Unknown error")}'}), 400
        
        bot_info = bot_result.get('result', {})
        
        # Test 2: Check chat access
        chat_url = f'https://api.telegram.org/bot{bot_token}/getChat'
        chat_response = requests.get(chat_url, params={'chat_id': chat_id}, timeout=10)
        
        chat_info = None
        if chat_response.status_code == 200:
            chat_result = chat_response.json()
            if chat_result.get('ok'):
                chat_info = chat_result.get('result', {})
        
        # Test 3: Send test message
        send_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        send_data = {
            'chat_id': chat_id,
            'text': '🧪 Тестовое сообщение от парсера\n\n✅ Подключение к Telegram работает корректно!'
        }
        send_response = requests.post(send_url, data=send_data, timeout=10)
        
        if send_response.status_code != 200:
            return jsonify({
                'status': 'error',
                'message': f'Не удалось отправить сообщение: {send_response.text}'
            }), 400
        
        send_result = send_response.json()
        if not send_result.get('ok'):
            return jsonify({
                'status': 'error',
                'message': f'Ошибка отправки: {send_result.get("description", "Unknown error")}'
            }), 400
        
        return jsonify({
            'status': 'success',
            'message': 'Подключение успешно, тестовое сообщение отправлено',
            'bot_info': {
                'name': bot_info.get('first_name', ''),
                'username': bot_info.get('username', ''),
                'id': bot_info.get('id', '')
            },
            'chat_info': {
                'title': chat_info.get('title', chat_info.get('first_name', 'Personal Chat')) if chat_info else 'Unknown',
                'id': chat_info.get('id', chat_id) if chat_info else chat_id
            } if chat_info else None
        })
        
    except requests.exceptions.Timeout:
        return jsonify({'status': 'error', 'message': 'Превышено время ожидания ответа от Telegram'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'error', 'message': f'Ошибка сети: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
@login_required  
def dashboard_stats():
    platform = request.args.get('platform', 'ozon')
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'ParserOzon'),
            user=os.getenv('DB_USER', 'GiperBox'),
            password=os.getenv('DB_PASS', 'Gingerik83'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        table = 'wb_prices' if platform == 'wb' else 'prices'
        cur = conn.cursor()
        
        print("[DEBUG] Querying total products...")
        # Total products (unique SKUs)
        cur.execute(f"SELECT COUNT(DISTINCT sku) FROM {table}")
        total_products = cur.fetchone()[0]
        
        print("[DEBUG] Querying products with prices...")
        # Products with prices - clean price_card and convert to numeric
        cur.execute(f"""
            SELECT COUNT(DISTINCT sku) FROM {table}
            WHERE price_card IS NOT NULL 
            AND NULLIF(REGEXP_REPLACE(price_card, '[^0-9]', '', 'g'), '')::NUMERIC > 0
        """)
        products_with_prices = cur.fetchone()[0]
        
        print("[DEBUG] Querying average price...")
        # Average price - clean and convert
        cur.execute(f"""
            SELECT AVG(NULLIF(REGEXP_REPLACE(price_card, '[^0-9]', '', 'g'), '')::NUMERIC) 
            FROM {table}
            WHERE price_card IS NOT NULL 
            AND NULLIF(REGEXP_REPLACE(price_card, '[^0-9]', '', 'g'), '')::NUMERIC > 0
        """)
        avg_price = cur.fetchone()[0] or 0
        
        print("[DEBUG] Querying total stores...")
        # Total stores
        cur.execute(f"SELECT COUNT(DISTINCT competitor_name) FROM {table} WHERE competitor_name IS NOT NULL")
        total_stores = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        print(f"[DEBUG] Stats: products={total_products}, with_prices={products_with_prices}, avg={avg_price}, stores={total_stores}")
        
        return jsonify({
            'total_products': total_products,
            'products_with_prices': products_with_prices,
            'avg_price': round(avg_price, 2),
            'total_stores': total_stores
        })
    except Exception as e:
        print(f"[ERROR] Dashboard stats failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/chart', methods=['GET'])
@login_required
def dashboard_chart():
    platform = request.args.get('platform', 'ozon')
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'ParserOzon'),
            user=os.getenv('DB_USER', 'GiperBox'),
            password=os.getenv('DB_PASS', 'Gingerik83'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        table = 'wb_prices' if platform == 'wb' else 'prices'
        cur = conn.cursor()
        
        # Get average price by competitor
        cur.execute(f"""
            SELECT 
                competitor_name,
                AVG(NULLIF(REGEXP_REPLACE(price_card, '[^0-9]', '', 'g'), '')::NUMERIC) as avg_price
            FROM {table} 
            WHERE competitor_name IS NOT NULL 
            AND price_card IS NOT NULL
            AND NULLIF(REGEXP_REPLACE(price_card, '[^0-9]', '', 'g'), '')::NUMERIC > 0
            GROUP BY competitor_name
            ORDER BY avg_price DESC
            LIMIT 10
        """)
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({
            'labels': [r[0] for r in results],
            'data': [round(float(r[1]), 2) for r in results]
        })
    except Exception as e:
        print(f"[ERROR] Chart data failed: {str(e)}")
        return jsonify({'labels': [], 'data': []}), 500

@app.route('/api/dashboard/items', methods=['GET'])
@login_required
def dashboard_items():
    platform = request.args.get('platform', 'ozon')
    search = request.args.get('search', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    store = request.args.get('store', '')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'ParserOzon'),
            user=os.getenv('DB_USER', 'GiperBox'),
            password=os.getenv('DB_PASS', 'Gingerik83'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        table = 'wb_prices' if platform == 'wb' else 'prices'
        cur = conn.cursor()
        
        # Include status for logic matching
        query = f"SELECT sku, name, competitor_name, price_card, price_nocard, price_old, created_at, status, sp_code FROM {table} WHERE 1=1"
        params = []
        
        if search:
            query += " AND (sku ILIKE %s OR name ILIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
        if store:
            query += " AND competitor_name = %s"
            params.append(store)
        if min_price:
            query += " AND NULLIF(REGEXP_REPLACE(price_nocard, '[^0-9]', '', 'g'), '')::NUMERIC >= %s"
            params.append(min_price)
        if max_price:
            query += " AND NULLIF(REGEXP_REPLACE(price_nocard, '[^0-9]', '', 'g'), '')::NUMERIC <= %s"
            params.append(max_price)
            
        # Count total for pagination
        count_query = f"SELECT COUNT(*) FROM ({query}) as sub"
        cur.execute(count_query, params)
        total_count = cur.fetchone()[0]
        
        # Add ordering (match Excel report: name, competitor_name for Ozon; sku, competitor for WB) and limit
        # Use NULLS LAST to ensure items with missing names/skus don't push content off the first page
        order_by = "name NULLS LAST, competitor_name" if platform == 'ozon' else "sku NULLS LAST, competitor_name"
        query += f" ORDER BY {order_by} LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        # Get stores list for filter
        cur.execute(f"SELECT DISTINCT competitor_name FROM {table} WHERE competitor_name IS NOT NULL ORDER BY competitor_name")
        stores = [r[0] for r in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        # Formatting function matching the report logic
        def format_val(val, status):
            st = str(status or '').upper()
            if 'OUT_OF_STOCK' in st:
                return 'Товар закончился'
            if 'ANTIBOT' in st:
                return 'Ошибка (Антибот)'
            if 'ERROR' in st:
                return 'Ошибка парсинга'
            if 'NO_PRICE' in st:
                return 'Нет цены'
            if val is None or str(val).lower() in ['none', 'nan', '']:
                return '---'
            return str(val)

        items = []
        for r in rows:
            status = r[7]
            items.append({
                'sku': r[0],
                'name': r[1],
                'seller': r[2],
                'promo': format_val(r[3], status),
                'price': format_val(r[4], status),
                'old': format_val(r[5], status),
                'updated': r[6].strftime('%d.%m %H:%M') if r[6] else '---',
                'sp_code': r[8] or '---'
            })
            
        return jsonify({
            'items': items,
            'total_pages': (total_count + per_page - 1) // per_page,
            'current_page': page,
            'stores': stores
        })
    except Exception as e:
        print(f"[ERROR] Table data failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/export', methods=['GET'])
@login_required
def dashboard_export():
    platform = request.args.get('platform', 'ozon')
    search = request.args.get('search', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    store = request.args.get('store', '')
    
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'ParserOzon'),
            user=os.getenv('DB_USER', 'GiperBox'),
            password=os.getenv('DB_PASS', 'Gingerik83'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        table = 'wb_prices' if platform == 'wb' else 'prices'
        
        query = f"SELECT sku as \"SKU\", competitor_name as \"Продавец\", price_card as \"Промо\", price_nocard as \"Цена\", price_old as \"Старая\" FROM {table} WHERE 1=1"
        params = []
        
        if search:
            query += " AND (sku ILIKE %s OR name ILIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
        if store:
            query += " AND competitor_name = %s"
            params.append(store)
        if min_price:
            query += " AND NULLIF(REGEXP_REPLACE(price_nocard, '[^0-9]', '', 'g'), '')::NUMERIC >= %s"
            params.append(min_price)
        if max_price:
            query += " AND NULLIF(REGEXP_REPLACE(price_nocard, '[^0-9]', '', 'g'), '')::NUMERIC <= %s"
            params.append(max_price)
            
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        
        # Convert date to string for Excel
        if not df.empty and 'Дата обновления' in df.columns:
            df['Дата обновления'] = df['Дата обновления'].dt.strftime('%Y-%m-%d %H:%M')

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
        
        output.seek(0)
        
        filename = f"report_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
    except Exception as e:
        print(f"[ERROR] Export failed: {str(e)}")
        return str(e), 500
@login_required
def get_schedules():
    """Get all schedules"""
    return jsonify(scheduler.load_schedules())

@app.route('/api/schedules', methods=['POST'])
@login_required
def save_schedules_api():
    """Save schedules and update scheduler"""
    try:
        schedules = request.json
        scheduler.save_schedules(schedules)
        scheduler.update_scheduler()
        return jsonify({'status': 'success', 'message': f'Сохранено {len(schedules)} расписаний и обновлен планировщик'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/schedules/status', methods=['GET'])
@login_required
def get_scheduler_status():
    """Get scheduler status and next run times"""
    try:
        next_runs = scheduler.get_next_run_times()
        return jsonify({
            'running': scheduler.scheduler.running,
            'jobs': next_runs
        })
    except Exception as e:
        return jsonify({'running': False, 'jobs': [], 'error': str(e)})

# User Management Routes
@app.route('/users')
@login_required
@permission_required('can_manage_users')
def users():
    """User management page (admin only)"""
    return render_template('users.html')

@app.route('/api/users', methods=['GET'])
@login_required
@permission_required('can_manage_users')
def get_users():
    """Get all users"""
    try:
        users = UserManager.get_all_users()
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
@login_required
@permission_required('can_manage_users')
def create_user():
    """Create new user"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        full_name = data.get('full_name', '')
        email = data.get('email', '')
        permissions = data.get('permissions', {})
        
        if not username or not password:
            return jsonify({'status': 'error', 'message': 'Username and password required'}), 400
        
        user_id = UserManager.create_user(username, password, full_name, email, permissions)
        return jsonify({'status': 'success', 'message': f'User created with ID {user_id}', 'user_id': user_id})
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
@permission_required('can_manage_users')
def update_user(user_id):
    """Update user"""
    try:
        data = request.json
        UserManager.update_user(user_id, data)
        return jsonify({'status': 'success', 'message': 'User updated'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@permission_required('can_manage_users')
def delete_user(user_id):
    """Delete user (soft delete - mark as inactive)"""
    try:
        # Prevent deleting yourself
        if str(user_id) == current_user.id:
            return jsonify({'status': 'error', 'message': 'Cannot delete your own account'}), 400
        
        UserManager.delete_user(user_id)
        return jsonify({'status': 'success', 'message': 'User deleted'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print(">>> Запуск веб-интерфейса парсера Ozon")
    print("="*70)
    print(f"URL: http://localhost:3455")
    print("Логин: admin (по умолчанию)")
    print("Пароль: admin (ИЗМЕНИТЕ В ПРОДАКШЕНЕ!)")
    print("="*70 + "\n")
    
    # Initialize scheduler
    print(">>> Инициализация планировщика задач...")
    scheduler.init_scheduler()
    
    app.run(host='0.0.0.0', port=3455, debug=False, threaded=True)
