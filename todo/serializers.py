from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Todo

class TodoSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Todo
        fields = ['id', 'task', 'date', 'is_completed', 'is_imported', 'username']
        read_only_fields = ['user']

class UserReportSerializer(serializers.ModelSerializer):
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    pending_tasks = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'total_tasks', 'completed_tasks', 'pending_tasks']

    def get_total_tasks(self, obj):
        request = self.context.get('request')
        date = request.GET.get('date') if request else None
        queryset = Todo.objects.filter(user=obj)
        if date:
            queryset = queryset.filter(date=date)
        return queryset.count()

    def get_completed_tasks(self, obj):
        request = self.context.get('request')
        date = request.GET.get('date') if request else None
        queryset = Todo.objects.filter(user=obj, is_completed=True)
        if date:
            queryset = queryset.filter(date=date)
        return queryset.count()

    def get_pending_tasks(self, obj):
        request = self.context.get('request')
        date = request.GET.get('date') if request else None
        queryset = Todo.objects.filter(user=obj, is_completed=False)
        if date:
            queryset = queryset.filter(date=date)
        return queryset.count()