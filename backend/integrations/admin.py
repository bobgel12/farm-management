from django.contrib import admin
from .models import IntegrationLog, IntegrationError, IntegrationHealth


@admin.register(IntegrationLog)
class IntegrationLogAdmin(admin.ModelAdmin):
    list_display = ['farm', 'integration_type', 'action', 'status', 'timestamp', 'execution_time']
    list_filter = ['integration_type', 'status', 'timestamp']
    search_fields = ['farm__name', 'action', 'message']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('farm', 'integration_type', 'action', 'status')
        }),
        ('Details', {
            'fields': ('message', 'data_points_processed', 'execution_time')
        }),
        ('Timestamps', {
            'fields': ('timestamp',)
        }),
    )


@admin.register(IntegrationError)
class IntegrationErrorAdmin(admin.ModelAdmin):
    list_display = ['farm', 'integration_type', 'error_type', 'resolved', 'created_at', 'resolved_at']
    list_filter = ['integration_type', 'error_type', 'resolved', 'created_at']
    search_fields = ['farm__name', 'error_type', 'error_message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Error Information', {
            'fields': ('farm', 'integration_type', 'error_type', 'error_message', 'error_code')
        }),
        ('Technical Details', {
            'fields': ('stack_trace',)
        }),
        ('Resolution', {
            'fields': ('resolved', 'resolved_at', 'resolved_by', 'resolution_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        for error in queryset:
            error.resolve(resolved_by=request.user.username, notes="Marked as resolved from admin")
        self.message_user(request, f"{queryset.count()} errors marked as resolved.")
    mark_as_resolved.short_description = "Mark selected errors as resolved"


@admin.register(IntegrationHealth)
class IntegrationHealthAdmin(admin.ModelAdmin):
    list_display = ['farm', 'integration_type', 'is_healthy', 'success_rate_24h', 'consecutive_failures', 'updated_at']
    list_filter = ['integration_type', 'is_healthy', 'updated_at']
    search_fields = ['farm__name']
    readonly_fields = ['updated_at']
    ordering = ['-updated_at']
    
    fieldsets = (
        ('Health Status', {
            'fields': ('farm', 'integration_type', 'is_healthy', 'consecutive_failures')
        }),
        ('Metrics', {
            'fields': ('success_rate_24h', 'average_response_time', 'last_successful_sync', 'last_attempted_sync')
        }),
        ('Error Information', {
            'fields': ('last_error',)
        }),
        ('Timestamps', {
            'fields': ('updated_at',)
        }),
    )