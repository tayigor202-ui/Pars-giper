"""Check if users exist in the database"""
from user_management import UserManager

try:
    users = UserManager.get_all_users()
    print(f"\n{'='*60}")
    print(f"НАЙДЕНО ПОЛЬЗОВАТЕЛЕЙ: {len(users)}")
    print('='*60)
    
    if users:
        for u in users:
            print(f"\nПользователь: {u['username']}")
            print(f"  Полное имя: {u.get('full_name', 'N/A')}")
            print(f"  Email: {u.get('email', 'N/A')}")
            print(f"  Активен: {u.get('is_active', True)}")
            print(f"  Последний вход: {u.get('last_login', 'Никогда')}")
            
            perms = u.get('permissions', {})
            if perms:
                print(f"  Права:")
                for perm, value in perms.items():
                    if value:
                        print(f"    ✓ {perm}")
    else:
        print("\n⚠️  ПОЛЬЗОВАТЕЛЕЙ НЕТ! Необходимо создать admin пользователя.")
        print("    Запустите: python init_users.py")
    
    print(f"\n{'='*60}\n")
    
except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
