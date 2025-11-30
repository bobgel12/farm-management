from django.contrib import admin
from .models import Issue, IssuePhoto, IssueComment


class IssuePhotoInline(admin.TabularInline):
    model = IssuePhoto
    extra = 0
    readonly_fields = ['uploaded_at', 'uploaded_by']


class IssueCommentInline(admin.TabularInline):
    model = IssueComment
    extra = 0
    readonly_fields = ['created_at', 'user']


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ['title', 'house', 'category', 'priority', 'status', 'reported_by', 'created_at']
    list_filter = ['status', 'category', 'priority', 'created_at', 'house__farm']
    search_fields = ['title', 'description', 'house__farm__name']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    raw_id_fields = ['house', 'reported_by', 'assigned_to', 'resolved_by', 'created_task']
    inlines = [IssuePhotoInline, IssueCommentInline]
    
    fieldsets = (
        ('Issue Details', {
            'fields': ('house', 'title', 'description', 'category', 'priority', 'status', 'location_in_house')
        }),
        ('Assignment', {
            'fields': ('reported_by', 'assigned_to', 'created_task')
        }),
        ('Resolution', {
            'fields': ('resolved_by', 'resolved_at', 'resolution_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(IssuePhoto)
class IssuePhotoAdmin(admin.ModelAdmin):
    list_display = ['issue', 'caption', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['issue__title', 'caption']
    raw_id_fields = ['issue', 'uploaded_by']


@admin.register(IssueComment)
class IssueCommentAdmin(admin.ModelAdmin):
    list_display = ['issue', 'user', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['issue__title', 'content']
    raw_id_fields = ['issue', 'user']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

