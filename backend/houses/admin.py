from django.contrib import admin
from .models import House, HouseMonitoringSnapshot, HouseAlarm, WaterConsumptionAlert


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


@admin.register(WaterConsumptionAlert)
class WaterConsumptionAlertAdmin(admin.ModelAdmin):
    list_display = [
        'house', 'farm', 'alert_date', 'current_consumption', 'baseline_consumption',
        'increase_percentage', 'severity', 'is_acknowledged', 'email_sent', 'created_at'
    ]
    list_filter = ['severity', 'is_acknowledged', 'email_sent', 'alert_date', 'farm']
    search_fields = ['house__farm__name', 'house__house_number', 'message']
    readonly_fields = ['created_at', 'updated_at', 'email_sent_at', 'acknowledged_at']
    date_hierarchy = 'alert_date'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('house', 'farm', 'alert_date', 'growth_day', 'severity')
        }),
        ('Consumption Data', {
            'fields': ('current_consumption', 'baseline_consumption', 'increase_percentage')
        }),
        ('Alert Details', {
            'fields': ('message', 'detection_method')
        }),
        ('Status', {
            'fields': ('is_acknowledged', 'acknowledged_by', 'acknowledged_at')
        }),
        ('Email Notification', {
            'fields': ('email_sent', 'email_sent_at', 'email_recipients')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['acknowledge_alerts', 'resend_email_alerts']
    
    def acknowledge_alerts(self, request, queryset):
        """Mark selected alerts as acknowledged"""
        from django.utils import timezone
        count = 0
        for alert in queryset:
            alert.acknowledge(user=request.user)
            count += 1
        self.message_user(request, f'{count} alerts marked as acknowledged.')
    acknowledge_alerts.short_description = 'Acknowledge selected alerts'
    
    def resend_email_alerts(self, request, queryset):
        """Resend email alerts for selected alerts"""
        from houses.services.water_alert_email_service import WaterAlertEmailService
        count = 0
        for alert in queryset:
            if WaterAlertEmailService.send_alert_email(alert):
                count += 1
        self.message_user(request, f'Resent {count} email alerts.')
    resend_email_alerts.short_description = 'Resend email alerts'
