from django.urls import path
from django.contrib import admin

from . import views
urlpatterns = [
    path('admin/login/', views.admin_login, name='admin_login'),
    path('signup/',views.signup,name='signup_api'),
    path('user/login/', views.user_login, name='user_login'),
    path('logout/', views.logout, name='logout_api'),
    path('admin-panel/', admin.site.urls),
    path('todos/', views.list_todos_by_date, name='list_todos'),
    path('todos/create/', views.create_todo, name='create_todo'),
    path('todos/<int:pk>/update/', views.update_todo, name='update_todo'),
    path('todos/<int:pk>/delete/', views.delete_todo, name='delete_todo'),
    path('todos/status/', views.filter_todos_by_status, name='filter_todos'),
    path('import/', views.import_todos, name='import_todos'),
    ]