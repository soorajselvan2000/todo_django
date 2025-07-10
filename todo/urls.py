from django.urls import path
from .views import create_task

urlpatterns = [
    path('create-task/', create_task, name='create-task'),
]
