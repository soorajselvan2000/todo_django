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
            timeout=300  # seconds
        )

from django.core.mail import send_mail

def send_overdue_task_emails():
    from .models import Todo
    today = now().date()
    overdue_tasks = Todo.objects.filter(date__lt=today, is_completed=False)

    for task in overdue_tasks:
        try:
            send_mail(
                subject="Overdue Task Reminder",
                message=f"Hi {task.user.username},\n\nYour task '{task.task}' is overdue!",
                from_email='todo-app@example.com',
                recipient_list=[task.user.email],  # send to task owner
                fail_silently=False,
            )
            print(f"Email sent to {task.user.email} for task '{task.task}'")
        except Exception as e:
            print(f"Failed to send email to {task.user.email}: {e}")