from django.urls import path
from . import views

urlpatterns = [
    path('tasks/', views.TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task-detail'),
    path('tasks/<int:task_id>/complete/', views.complete_task, name='complete-task'),
    path('houses/<int:house_id>/tasks/', views.house_tasks, name='house-tasks'),
    path('houses/<int:house_id>/tasks/today/', views.today_tasks, name='today-tasks'),
    path('houses/<int:house_id>/tasks/upcoming/', views.upcoming_tasks, name='upcoming-tasks'),
    path('houses/<int:house_id>/tasks/generate/', views.generate_tasks, name='generate-tasks'),
    path('tasks/dashboard/', views.task_dashboard, name='task-dashboard'),
    path('recurring-tasks/', views.RecurringTaskListCreateView.as_view(), name='recurring-task-list'),
    path('recurring-tasks/<int:pk>/', views.RecurringTaskDetailView.as_view(), name='recurring-task-detail'),
    path('tasks/send-test-email/', views.send_test_email, name='send-test-email'),
    path('tasks/send-daily-tasks/', views.send_daily_tasks, name='send-daily-tasks'),
    path('tasks/email-history/', views.email_history, name='email-history'),
]
