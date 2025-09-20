from django.contrib import admin
from .models import Task, RecurringTask


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['house', 'day_offset', 'task_name', 'task_type', 'is_completed', 'completed_at']
    list_filter = ['task_type', 'is_completed', 'day_offset', 'house__farm']
    search_fields = ['task_name', 'description', 'house__farm__name', 'house__house_number']
    readonly_fields = ['created_at', 'updated_at']
    list_select_related = ['house', 'house__farm']
    ordering = ['house', 'day_offset', 'task_name']


@admin.register(RecurringTask)
class RecurringTaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'frequency', 'day_of_week', 'time', 'is_active']
    list_filter = ['frequency', 'is_active', 'day_of_week']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
