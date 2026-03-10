from django.contrib import admin
from .models import Visitor, Visit, AuditLog

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'email', 'organization', 'created_at']
    search_fields = ['full_name', 'phone', 'email', 'organization']
    list_filter = ['created_at', 'organization']
    ordering = ['-created_at']

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ['visitor', 'location', 'purpose', 'host', 'check_in_time', 'check_out_time', 'status']
    search_fields = ['visitor__full_name', 'purpose', 'host']
    list_filter = ['status', 'check_in_time', 'location']
    ordering = ['-check_in_time']
    readonly_fields = ['check_in_time', 'check_out_time']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'visitor', 'visit', 'timestamp']
    search_fields = ['user__username', 'action', 'visitor__full_name']
    list_filter = ['action', 'timestamp']
    ordering = ['-timestamp']
    readonly_fields = ['user', 'action', 'visitor', 'visit', 'timestamp', 'notes', 'ip_address']
