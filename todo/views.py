from django.contrib.auth import authenticate,login
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from django.contrib.auth.forms import UserCreationForm
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from .forms import TodoForm
from .serializers import TodoSerializer,UserReportSerializer
from .models import Todo
from rest_framework.response import Response
from rest_framework import status
from .serializers import TodoSerializer
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User

# Signup
@api_view(['POST'])
@permission_classes((AllowAny,))
def signup(request):
    form = UserCreationForm(data=request.data)
    if form.is_valid():
        user = form.save(commit=False)
        email = request.data.get("email")
        if email:
            user.email = email
        user.save()
        return Response({"message": "Account created successfully"}, status=status.HTTP_201_CREATED)
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

from rest_framework import status
from .models import UserProfile

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upgrade_to_premium(request):
    """Upgrade the logged-in user to premium"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        profile.is_premium = True
        profile.save()
        return Response({"message": "You are now a premium user!"}, status=status.HTTP_200_OK)
    except UserProfile.DoesNotExist:
        return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

# Create todo
from django.utils.timezone import now
from .models import UserActionLog
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def create_todo(request):
#     today = now().date()

#     # ✅ Count only today's non-deleted todos
#     created_today_count = Todo.objects.filter(
#         user=request.user,
#         date=today,
#         is_deleted=False
#     ).count()

#     if created_today_count >= 2:
#         return Response(
#             {"error": "Daily limit of 2 tasks reached."},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     serializer = TodoSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save(user=request.user)
#         UserActionLog.objects.create(user=request.user, action='added', todo=serializer.instance)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
    
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_todo(request):
    today = now().date()

    # ✅ Check premium status
    is_premium = hasattr(request.user, "userprofile") and request.user.userprofile.is_premium
    daily_limit = 1000 if is_premium else 12

    created_today_count = Todo.objects.filter(
        user=request.user,
        date=today,
        is_deleted=False
    ).count()

    if created_today_count >= daily_limit:
        return Response(
            {"error": f"Daily limit of {daily_limit} tasks reached."},
            status=status.HTTP_400_BAD_REQUEST
        )

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

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Todo

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def send_expired_todos_email(request):
    user = request.user

    if not user.email:
        return Response({'error': 'User does not have an email address'}, status=status.HTTP_400_BAD_REQUEST)

    # Get all expired todos for this user (past due date and not deleted)
    expired_todos = Todo.objects.filter(user=user, date__lt=timezone.now(), is_deleted=False)

    if not expired_todos.exists():
        return Response({'message': 'No expired todos to send'}, status=status.HTTP_200_OK)

    # Prepare email content
    subject = 'Your Expired Todos'
    message_lines = ['The following todos have expired:\n']
    for todo in expired_todos:
        message_lines.append(f"- {todo.task} (Due: {todo.date.strftime('%Y-%m-%d %H:%M')})")

    conclusion = "\n\nPlease take necessary action on these tasks.\n\nBest regards,\nTodo App Team"
    message = f'Dear {user}\n\n'  + "\n".join(message_lines) + conclusion
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    try:
        send_mail(subject, message, from_email, recipient_list)
        return Response({'message': 'Expired todos sent via email successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': f'Failed to send email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

# importing todo as CSV file
import csv
import io

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_todos(request):
    file = request.FILES.get("file")
    if not file:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
    if not file.name.endswith(".csv"):
        return Response({"error": "File must be CSV"}, status=status.HTTP_400_BAD_REQUEST)

    decoded_file = file.read().decode("utf-8")
    io_string = io.StringIO(decoded_file)
    reader = csv.DictReader(io_string)

    created_count = 0
    for row in reader:
        task, date = row.get("task"), row.get("date")
        if task and date:
            todo = Todo.objects.create(user=request.user, task=task, date=date, is_completed=False, is_imported=True)
            print("IMPORT LOGGING:", task, date)
            UserActionLog.objects.create(user=request.user, action='imported', todo=todo)

            created_count += 1

    return Response({"message": f"{created_count} todos imported successfully."}, status=200)

from django.http import HttpResponse, JsonResponse
from io import StringIO
from django.utils import timezone

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_todos(request):
    """
    Export todos in various formats - matches frontend API structure
    Expected URL: /api/todos/export/?format=csv (or json, txt, mysql)
    """
    format_type = request.GET.get('format', 'json').lower()
    
    # Get user's todos
    todos = Todo.objects.filter(user=request.user, is_deleted=False)
    
    if not todos.exists():
        return JsonResponse({"error": "No todos to export"}, status=404)
    
    # Prepare data in the exact format expected by frontend
    data = []
    for todo in todos:
        data.append({
            "id": todo.id,
            "task": todo.task,
            "date": str(todo.date),
            "is_completed": todo.is_completed,
            "is_imported": todo.is_imported,
            "username": todo.user.username,
            # Add any other fields your frontend expects
        })
    
    # Log the export action for each todo
    for todo in todos:
        UserActionLog.objects.create(
            user=request.user,
            action="exported",
            todo=todo
        )
    
    # Handle different export formats
    if format_type == 'csv':
        return export_csv(data)
    elif format_type == 'json':
        return export_json(data)
    elif format_type == 'txt':
        return export_txt(data)
    elif format_type == 'mysql':
        return export_mysql(data, request.user)
    else:
        return JsonResponse({"error": "Invalid format. Use: csv, json, txt, mysql"}, status=400)


def export_csv(data):
    """Export data as CSV"""
    if not data:
        return JsonResponse({"error": "No data to export"}, status=404)
    
    # Create CSV content
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    
    response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="todos.csv"'
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'
    
    return response


def export_json(data):
    """Export data as JSON"""
    return JsonResponse(data, safe=False, json_dumps_params={'indent': 2})


def export_txt(data):
    """Export data as TXT"""
    if not data:
        return JsonResponse({"error": "No data to export"}, status=404)
    
    content = ""
    for item in data:
        content += f"ID: {item['id']}\n"
        content += f"Task: {item['task']}\n"
        content += f"Date: {item['date']}\n"
        content += f"Completed: {item['is_completed']}\n"
        content += f"Username: {item['username']}\n"
        content += "-" * 40 + "\n\n"
    
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="todos.txt"'
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'
    
    return response


def export_mysql(data, user):
    """Export data as MySQL insert statements"""
    if not data:
        return JsonResponse({"error": "No data to export"}, status=404)
    
    content = "-- MySQL export generated on " + str(timezone.now()) + "\n\n"
    content += "-- Exported by: " + user.username + "\n\n"
    
    for item in data:
        # Escape single quotes in task
        task_escaped = item['task'].replace("'", "''") if item['task'] else ''
        
        sql = (
            f"INSERT INTO todos (id, task, date, is_completed, username) VALUES ("
            f"{item['id']}, "
            f"'{task_escaped}', "
            f"'{item['date']}', "
            f"{1 if item['is_completed'] else 0}, "
            f"'{item['username']}'"
            f");\n"
        )
        content += sql
    
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="todos.sql"'
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'
    
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_todos_log(request):
    """
    Log export action - matches frontend API structure
    Expected URL: /api/todos/export/log/ (POST)
    """
    try:
        # Log a general export action (without specific todo)
        UserActionLog.objects.create(
            user=request.user,
            action="exported"
        )
        
        return JsonResponse({
            "message": "Export action logged successfully",
            "status": "success"
        })
    
    except Exception as e:
        return JsonResponse({
            "error": f"Failed to log export action: {str(e)}",
            "status": "error"
        }, status=500)


# Logout for User and Admin
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        request.user.auth_token.delete()
    except:
        return Response({'error': 'Something went wrong'}, status=HTTP_400_BAD_REQUEST)
    return Response({"message": "Successfully logged out"}, status=HTTP_200_OK)

# Task scheduler
from django.http import JsonResponse
from django_apscheduler.models import DjangoJob

def list_jobs(request):
    jobs = DjangoJob.objects.all().values("id", "next_run_time")
    return JsonResponse(list(jobs), safe=False)

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
from django.db.models import Count, Q
from rest_framework import status

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_user_report(request):
    if not request.user.is_superuser:
        return Response({'error': 'Unauthorized. Only admin can access this.'}, status=status.HTTP_403_FORBIDDEN)

    date = request.GET.get('date')

    # ✅ Annotate with counts
    users = User.objects.filter(is_superuser=False).annotate(
        total_tasks=Count('todo', filter=Q(todo__is_deleted=False) & (Q(todo__date=date) if date else Q())),
        completed_tasks=Count('todo', filter=Q(todo__is_deleted=False, todo__is_completed=True) & (Q(todo__date=date) if date else Q())),
        pending_tasks=Count('todo', filter=Q(todo__is_deleted=False, todo__is_completed=False) & (Q(todo__date=date) if date else Q()))
    ).order_by('-total_tasks')  # ✅ Sort users by most → least tasks

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


# Testing:
# todo/views.py
from django.http import JsonResponse
from .Jobs import send_task_reminders

def run_reminder_now(request):
    send_task_reminders()
    return JsonResponse({"status": "Job executed manually!"})
