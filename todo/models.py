from django.db import models
from django.contrib.auth.models import User

class Todo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    task = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.date} - {self.task}"

    edit_count = models.IntegerField(default=0)
    last_edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_todos')
    last_edited_at = models.DateTimeField(null=True, blank=True)
    last_edited_field = models.CharField(max_length=100, blank=True, null=True)
    last_edit_detail = models.TextField(blank=True, null=True)  # ← what's edited
