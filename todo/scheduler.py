# todo/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from .Jobs import send_task_reminders

scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")

def start():
    """
    Starts the APScheduler with our custom jobs.
    Runs in background when Django is running.
    """
    try:
        scheduler.add_job(
            send_task_reminders,          # ✅ call the reminder job
            trigger="interval",
            minutes=1,                    # 🔹 change to 1440 (once per day)
            id="send_task_reminders",
            replace_existing=True,        # prevents duplicate jobs
        )

        register_events(scheduler)
        scheduler.start()
        print("✅ Scheduler started successfully!")

    except Exception as e:
        print(f"⚠️ Error starting scheduler: {e}")
