from django.contrib.auth import authenticate,login
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from django.contrib.auth.forms import UserCreationForm
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .forms import TodoForm
from .serializers import TodoSerializer,UserReportSerializer
from .models import Todo
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import TodoSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Todo
from .forms import TodoForm

# Normal user Signup API
@api_view(['POST'])
@permission_classes((AllowAny,))
def signup(request):
    form = UserCreationForm(data=request.data)
    if form.is_valid():
        user = form.save()
        return Response("account created successfully", status=status.HTTP_201_CREATED)
    return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

# Normal user login API
@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def user_login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    if not username or not password:
        return Response({'error': 'Username and password required'}, status=HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)

    if user and not user.is_superuser:
        login(request, user)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'message': 'User logged in'}, status=HTTP_200_OK)

    return Response({'error': 'Invalid user credentials'}, status=HTTP_404_NOT_FOUND)

# Create todo
from .models import UserActionLog
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_todo(request):
    serializer = TodoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        UserActionLog.objects.create(user=request.user, action='added', todo=serializer.instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Filter todos by status[completed or pending]
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def filter_todos_by_status(request):
    status_param = request.GET.get('status')

    if status_param == 'completed':
        todos = Todo.objects.filter(user=request.user, is_completed=True, is_deleted=False)
    elif status_param == 'pending':
        todos = Todo.objects.filter(user=request.user, is_completed=False, is_deleted=False)
    else:  # 'all' or missing
        todos = Todo.objects.filter(user=request.user, is_deleted=False)

    serializer = TodoSerializer(todos, many=True)
    return Response(serializer.data)

# Search todo by Date
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_todos_by_date(request):
    date = request.GET.get('date')
    if not date:
        return Response({'error': 'Date parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    todos = Todo.objects.filter(user=request.user, date=date, is_deleted = False)
    serializer = TodoSerializer(todos, many=True)
    return Response(serializer.data)

# Update todo
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_todo(request, pk):
    try:
        todo = Todo.objects.get(pk=pk, user=request.user)
    except Todo.DoesNotExist:
        return Response({'error': 'Todo not found'}, status=status.HTTP_404_NOT_FOUND)
    
    old_task = todo.task
    old_is_completed = todo.is_completed

    form = TodoForm(request.data, instance=todo)
    if form.is_valid():
        form.save()

        new_task = request.data.get('task', old_task)
        new_is_completed = request.data.get('is_completed', old_is_completed)

        # Track what was changed
        if old_task != new_task:
            todo.last_edited_field = 'task'
            todo.last_edit_detail = f"task changed from '{old_task}' to '{new_task}'"
            # Log edited action
            UserActionLog.objects.create(user=request.user, action='edited', todo=todo)

        elif str(old_is_completed).lower() != str(new_is_completed).lower():
            todo.last_edited_field = 'is_completed'
            todo.last_edit_detail = f"is_completed changed from '{old_is_completed}' to '{new_is_completed}'"
            # Log edited action
            UserActionLog.objects.create(user=request.user, action='edited', todo=todo)
            # Log completed action if marked True
            if str(new_is_completed).lower() == 'true':
                UserActionLog.objects.create(user=request.user, action='completed', todo=todo)
        else:
            todo.last_edited_field = 'nothing'
            todo.last_edit_detail = 'No actual change in values'

        todo.edit_count += 1
        todo.last_edited_by = request.user
        todo.save()

        return Response({'message': 'Todo updated successfully'}, status=status.HTTP_200_OK)
    
    return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

# Delete todo
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_todo(request, pk):
    try:
        todo = Todo.objects.get(pk=pk, user=request.user, is_deleted=False)
    except Todo.DoesNotExist:
        return Response({'error': 'Todo not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Soft delete
    todo.is_deleted = True
    todo.save()

    # Log the deletion
    UserActionLog.objects.create(
        user=request.user,
        action='deleted',
        todo=todo
    )

    return Response({'message': 'Todo deleted successfully'}, status=status.HTTP_200_OK)

# Logout for User and Admin
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        request.user.auth_token.delete()
    except:
        return Response({'error': 'Something went wrong'}, status=HTTP_400_BAD_REQUEST)
    return Response({"message": "Successfully logged out"}, status=HTTP_200_OK)

# Admin - login API
@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def admin_login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({'error': 'Username and password required'}, status=HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)

    if user and user.is_superuser:
        login(request, user)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'message': 'Admin logged in'}, status=HTTP_200_OK)
    return Response({'error': 'Invalid admin credentials'}, status=HTTP_404_NOT_FOUND)

# Admin - User Report
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_user_report(request):
    if not request.user.is_superuser:
        return Response({'error': 'Unauthorized. Only admin can access this.'}, status=status.HTTP_403_FORBIDDEN)

    from django.contrib.auth.models import User
    users = User.objects.filter(is_superuser = False)
    serializer = UserReportSerializer(users, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

# Admin - User Usage Statistics Report
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_user_usage_stats(request):
    if not request.user.is_superuser:
        return Response({'error': 'Unauthorized. Only admin can access this.'}, status=403)

    from django.contrib.auth.models import User
    from .models import UserActionLog

    users = User.objects.filter(is_superuser=False)
    data = []

    for user in users:
        user_logs = UserActionLog.objects.filter(user=user)
        data.append({
            "username": user.username,
            "added_tasks": user_logs.filter(action='added').count(),
            "deleted_tasks": user_logs.filter(action='deleted').count(),
            "completed_tasks": user_logs.filter(action='completed').count(),
            "edited_tasks": user_logs.filter(action='edited').count(),
            "imported_tasks": user_logs.filter(action='imported').count(),
            "exported_tasks": user_logs.filter(action='exported').count(),
        })

    return Response(data, status=200)















@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_todos(request):
    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'No file provided'}, status=400)

    ext = file.name.split('.')[-1].lower()

    if ext == 'json':
        import json
        data = json.load(file)
        for item in data:
            Todo.objects.create(user=request.user, **item)

    elif ext == 'csv':
        import csv
        decoded = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded)
        for row in reader:
            Todo.objects.create(user=request.user, **row)

    elif ext == 'txt':
        lines = file.read().decode('utf-8').splitlines()
        for line in lines:
            Todo.objects.create(user=request.user, task=line, date=date.today())

    elif ext == 'sql':
        # WARNING: Not safe to run SQL queries directly unless parsed
        return Response({'error': 'SQL import not supported for safety'}, status=400)

    else:
        return Response({'error': 'Unsupported file format'}, status=400)

    return Response({'message': 'Todos imported successfully'})
