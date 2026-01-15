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

def run_parser():
    """Execute run_all.bat"""
    print(f"[SCHEDULER] Starting parser at {datetime.now()}")
    try:
        subprocess.Popen(['cmd', '/c', 'start', 'cmd', '/c', 'run_all.bat'], shell=False)
        print("[SCHEDULER] Parser launched successfully")
    except Exception as e:
        print(f"[SCHEDULER] Error launching parser: {e}")

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
                id=f"schedule_{schedule['id']}",
                name=f"Parser at {schedule['time']} on {days}"
            )
            print(f"[SCHEDULER] Added job: {schedule['time']} on {days}")

def init_scheduler():
    """Initialize the scheduler"""
    update_scheduler()
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
