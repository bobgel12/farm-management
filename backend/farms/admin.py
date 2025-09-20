from django.contrib import admin
from .models import Farm, Worker


class WorkerInline(admin.TabularInline):
    model = Worker
    extra = 1
    fields = ['name', 'email', 'phone', 'role', 'is_active', 'receive_daily_tasks']


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'contact_person', 'is_active', 'total_houses', 'active_houses']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'location', 'contact_person']
    readonly_fields = ['created_at', 'updated_at', 'total_houses', 'active_houses']
    inlines = [WorkerInline]


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'farm', 'role', 'is_active', 'receive_daily_tasks', 'created_at']
    list_filter = ['is_active', 'receive_daily_tasks', 'farm', 'role', 'created_at']
    search_fields = ['name', 'email', 'farm__name']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active', 'receive_daily_tasks']
