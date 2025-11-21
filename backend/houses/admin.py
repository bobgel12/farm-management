from django.contrib import admin
from .models import House, HouseMonitoringSnapshot, HouseAlarm


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ['farm', 'house_number', 'chicken_in_date', 'chicken_out_date', 'current_day', 'status', 'is_active']
    list_filter = ['farm', 'is_active', 'chicken_in_date']
    search_fields = ['farm__name', 'house_number']
    readonly_fields = ['current_day', 'days_remaining', 'status', 'created_at', 'updated_at']
    list_select_related = ['farm']


@admin.register(HouseMonitoringSnapshot)
class HouseMonitoringSnapshotAdmin(admin.ModelAdmin):
    list_display = ['house', 'timestamp', 'average_temperature', 'humidity', 'growth_day', 'alarm_status', 'is_connected']
    list_filter = ['alarm_status', 'connection_status', 'timestamp']
    search_fields = ['house__farm__name', 'house__house_number']
    readonly_fields = ['timestamp', 'created_at']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']


@admin.register(HouseAlarm)
class HouseAlarmAdmin(admin.ModelAdmin):
    list_display = ['house', 'alarm_type', 'severity', 'message', 'is_active', 'is_resolved', 'timestamp']
    list_filter = ['alarm_type', 'severity', 'is_active', 'is_resolved', 'timestamp']
    search_fields = ['house__farm__name', 'house__house_number', 'message']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(
            is_resolved=True,
            is_active=False,
            resolved_at=timezone.now(),
            resolved_by=request.user.username
        )
        self.message_user(request, f'{count} alarms marked as resolved.')
    mark_as_resolved.short_description = 'Mark selected alarms as resolved'
