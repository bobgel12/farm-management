from django.contrib import admin
from .models import Farm, Worker, MortalityRecord


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


@admin.register(MortalityRecord)
class MortalityRecordAdmin(admin.ModelAdmin):
    list_display = ['flock', 'house', 'record_date', 'total_deaths', 'recorded_by', 'created_at']
    list_filter = ['record_date', 'house__farm', 'created_at']
    search_fields = ['flock__flock_code', 'house__farm__name', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['flock', 'house', 'recorded_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('flock', 'house', 'record_date', 'total_deaths')
        }),
        ('Detailed Breakdown', {
            'fields': (
                'disease_deaths', 'culling_deaths', 'accident_deaths',
                'heat_stress_deaths', 'cold_stress_deaths', 'unknown_deaths', 'other_deaths'
            ),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes', 'recorded_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
