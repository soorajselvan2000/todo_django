from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from django.contrib.auth.forms import UserCreationForm
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .forms import TodoForm
from .serializers import TodoSerializer
from .models import Todo
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import TodoSerializer

@api_view(['POST'])
@permission_classes((AllowAny,))
def signup(request):
    form = UserCreationForm(data=request.data)
    if form.is_valid():
        user = form.save()
        return Response("account created successfully", status=status.HTTP_201_CREATED)
    return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(["POST"])
@permission_classes((AllowAny,))
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    if username is None or password is None:
        return Response({'error': 'Please provide both username and password'},
                        status=HTTP_400_BAD_REQUEST)
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid Credentials'},
                        status=HTTP_404_NOT_FOUND)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key},status=HTTP_200_OK)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        request.user.auth_token.delete()
    except:
        return Response({'error': 'Something went wrong'}, status=HTTP_400_BAD_REQUEST)
    return Response({"message": "Successfully logged out"}, status=HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_todo(request):
    serializer = TodoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_todos_by_date(request):
    date = request.GET.get('date')
    if not date:
        return Response({'error': 'Date parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    todos = Todo.objects.filter(user=request.user, date=date)
    serializer = TodoSerializer(todos, many=True)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_todo(request, pk):
    try:
        todo = Todo.objects.get(pk=pk, user=request.user)
    except Todo.DoesNotExist:
        return Response({'error': 'Todo not found'}, status=status.HTTP_404_NOT_FOUND)
    
    form = TodoForm(request.data, instance=todo)
    if form.is_valid():
        form.save()
        return Response({'message': 'Todo updated successfully'}, status=status.HTTP_200_OK)
    return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_todo(request, pk):
    try:
        todo = Todo.objects.get(pk=pk, user=request.user)
    except Todo.DoesNotExist:
        return Response({'error': 'Todo not found'}, status=status.HTTP_404_NOT_FOUND)
    
    todo.delete()
    return Response({'message': 'Todo deleted successfully'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def filter_todos_by_status(request):
    status_param = request.GET.get('status')

    if status_param == 'completed':
        todos = Todo.objects.filter(user=request.user, is_completed=True)
    elif status_param == 'pending':
        todos = Todo.objects.filter(user=request.user, is_completed=False)
    else:  # 'all' or missing
        todos = Todo.objects.filter(user=request.user)

    serializer = TodoSerializer(todos, many=True)
    return Response(serializer.data)

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

