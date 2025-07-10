from django.db import models

class Task(models.Model):
    text = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    date = models.DateField()

    def __str__(self):
        return self.text
