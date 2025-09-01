from django.urls import path
from django.contrib import admin

from . import views
urlpatterns = [
    # User
    path('signup/',views.signup,name='signup_api'),
    path('user/login/', views.user_login, name='user_login'),
    path('logout/', views.logout, name='logout_api'), #Also for admin
    path("upgrade-to-premium/", views.upgrade_to_premium, name="upgrade_to_premium"),
    path('todos/create/', views.create_todo, name='create_todo'),
    path('todos/', views.list_todos_by_date, name='list_todos'),
    path('todos/status/', views.filter_todos_by_status, name='filter_todos'),
    path('todos/<int:pk>/update/', views.update_todo, name='update_todo'),
    path('todos/<int:pk>/delete/', views.delete_todo, name='delete_todo'),
    path('todos/expire/', views.send_expired_todos_email, name='expire_todos'),
    path("todos/import/", views.import_todos, name="import-todos"),
    path('todos/export/', views.export_todos, name='export_todos'),
    path('todos/export/log/', views.export_todos_log, name='export_todos_log'),
    path("jobs/", views.list_jobs, name="list_jobs"),
    # Admin
    path('admin-panel/', admin.site.urls),
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/report/', views.admin_user_report, name='admin_user_report'),
    path('admin/usage-stats/', views.admin_user_usage_stats, name='admin_user_usage_stats'),
    



    path("run-job/", views.run_reminder_now, name="run_reminder_now"),
    ]