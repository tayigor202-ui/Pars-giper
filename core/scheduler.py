import os
import json
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import subprocess

scheduler = BackgroundScheduler()
SCHEDULES_FILE = 'schedules.json'

def load_schedules():
    """Load schedules from JSON file"""
    if os.path.exists(SCHEDULES_FILE):
        with open(SCHEDULES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_schedules(schedules):
    """Save schedules to JSON file"""
    with open(SCHEDULES_FILE, 'w', encoding='utf-8') as f:
        json.dump(schedules, f, ensure_ascii=False, indent=2)

def run_parser(platform='ozon'):
    """Execute parser script directly"""
    print(f"[SCHEDULER] Starting {platform} parser at {datetime.now()}")
    try:
        import sys
        if platform == 'wb':
            script_name = 'wb_parser_production.py'
        else:
            script_name = 'ozon_parser_production_final.py'
            
        # Path relative to core/scheduler.py is ../parsers/script_name
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_path = os.path.join(base_dir, 'parsers', script_name)
        
        # Run in separate window using 'start' on Windows
        cmd = f'start "{platform.upper()} Parser" cmd /c "{sys.executable} {script_path}"'
        subprocess.Popen(cmd, shell=True)
        print(f"[SCHEDULER] {platform.upper()} Parser launched successfully")
    except Exception as e:
        print(f"[SCHEDULER] Error launching {platform} parser: {e}")

def update_scheduler():
    """Update scheduler jobs based on saved schedules"""
    # Remove all existing jobs
    scheduler.remove_all_jobs()
    
    schedules = load_schedules()
    for schedule in schedules:
        if not schedule.get('enabled'):
            continue
            
        time_parts = schedule['time'].split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        platform = schedule.get('platform', 'ozon')
        
        # Convert day indices to cron format
        # 0=Mon, 1=Tue, ..., 6=Sun -> mon,tue,wed,thu,fri,sat,sun
        day_names = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        days = ','.join([day_names[d] for d in schedule['days']])
        
        if days:
            trigger = CronTrigger(
                day_of_week=days,
                hour=hour,
                minute=minute
            )
            scheduler.add_job(
                run_parser,
                trigger=trigger,
                args=[platform],
                id=f"schedule_{schedule['id']}",
                name=f"{platform.upper()} Parser at {schedule['time']} on {days}"
            )
            print(f"[SCHEDULER] Added job: {platform.upper()} at {schedule['time']} on {days}")

def check_git_updates():
    """Check for updates in Git and pull if available"""
    from web_app import load_config, save_config
    
    config = load_config()
    if not config.get('auto_update', False):
        return

    print(f"[AUTO-UPDATER] Checking for updates at {datetime.now()}...")
    try:
        # 0. Check if it's a git repo
        if not os.path.exists('.git'):
            print("[AUTO-UPDATER] Error: Not a Git repository. Auto-update disabled.")
            return

        # 1. Fetch changes
        subprocess.run(['git', 'fetch', 'origin'], check=True, capture_output=True)
        
        # 2. Compare hashes
        local_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        remote_hash = subprocess.check_output(['git', 'rev-parse', '@{u}'], text=True).strip()
        
        # Update last check time in config
        config['last_update_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_config(config)
        
        if local_hash != remote_hash:
            print(f"[AUTO-UPDATER] Updates found! Pulling changes...")
            pull_result = subprocess.run(['git', 'pull', 'origin', 'main'], check=True, capture_output=True, text=True)
            print(f"[AUTO-UPDATER] Pull successful: {pull_result.stdout[:100]}...")
            
            # 3. Check if important files changed
            important_files = ['web_app.py', 'scheduler.py', 'user_management.py']
            changed_files = subprocess.check_output(['git', 'diff', '--name-only', local_hash, remote_hash], text=True)
            
            if any(f in changed_files for f in important_files):
                print("[AUTO-UPDATER] Critical files changed. Restarting application...")
                # Path to restart_app.bat in root
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                restart_script = os.path.join(base_dir, 'restart_app.bat')
                if os.path.exists(restart_script):
                    subprocess.Popen(['cmd', '/c', 'start', 'cmd', '/c', f'"{restart_script}"'], shell=True)
        else:
            print("[AUTO-UPDATER] Already up to date.")
            
    except Exception as e:
        print(f"[AUTO-UPDATER] Update check failed: {e}")
        config['last_update_check'] = f"Ошибка: {datetime.now().strftime('%H:%M:%S')}"
        save_config(config)

def init_scheduler():
    """Initialize the scheduler"""
    update_scheduler()
    
    # Add auto-updater task (every 60 minutes)
    scheduler.add_job(
        check_git_updates,
        trigger='interval',
        minutes=60,
        id='git_autoupdate',
        name='Git Auto-Update Check'
    )
    print("[SCHEDULER] Registered Git Auto-Update job (60 min interval)")
    
    if not scheduler.running:
        scheduler.start()
        print("[SCHEDULER] Background scheduler started")

def get_next_run_times():
    """Get next run times for all jobs"""
    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            'name': job.name,
            'next_run': next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else 'N/A'
        })
    return jobs
