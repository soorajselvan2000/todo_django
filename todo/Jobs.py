from plyer import notification
from django.utils.timezone import now, timedelta
from .models import Todo

def send_task_reminders():
    tomorrow = now().date() + timedelta(days=1)
    tasks = Todo.objects.filter(date=tomorrow)

    for todo in tasks:
        notification.notify(
            title="Task Reminder",
            message=f"Hi {todo.user.username}, your task '{todo.task}' is due tomorrow.",
            timeout=600  # seconds
        )
