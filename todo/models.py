from django.db import models
from django.contrib.auth.models import User

class Todo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    task = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_imported = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.date} - {self.task}"

    edit_count = models.IntegerField(default=0)
    last_edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_todos')
    last_edited_at = models.DateTimeField(null=True, blank=True)
    last_edited_field = models.CharField(max_length=100, blank=True, null=True)
    last_edit_detail = models.TextField(blank=True, null=True)

class UserActionLog(models.Model):
    ACTION_CHOICES = [
        ('added', 'Added Task'),
        ('deleted', 'Deleted Task'),
        ('completed', 'Completed Task'),
        ('edited', 'Edited Task'),
        ('imported', 'Imported Tasks'),
        ('exported', 'Exported Tasks'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    todo = models.ForeignKey('Todo', on_delete=models.SET_NULL, null=True, blank=True)  # Optional link

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"
    
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_premium = models.BooleanField(default=False)  # ✅ premium flag

    def __str__(self):
        return f"{self.user.username} - {'Premium' if self.is_premium else 'Free'}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
