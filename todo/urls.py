from django.urls import path
from . import views
urlpatterns = [
    path('signup/',views.signup,name='signup_api'),
    path('login/', views.login, name='login_api'),
    path('logout/', views.logout, name='logout_api'),
    path('todos/', views.list_todos_by_date, name='list_todos'),
    path('todos/create/', views.create_todo, name='create_todo'),
    path('todos/<int:pk>/update/', views.update_todo, name='update_todo'),
    path('todos/<int:pk>/delete/', views.delete_todo, name='delete_todo'),
    path('todos/status/', views.filter_todos_by_status, name='filter_todos'),
    path('import/', views.import_todos, name='import_todos'),
    ]