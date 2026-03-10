from django.contrib import admin
from .models import Pass

@admin.register(Pass)
class PassAdmin(admin.ModelAdmin):
    list_display = ['pass_number', 'visitor_name', 'visitor_type', 'company_name', 'purpose', 'location', 'status', 'check_in_time']
    search_fields = ['pass_number', 'visitor_name', 'company_name', 'purpose', 'host_name']
    list_filter = ['status', 'visitor_type', 'location', 'check_in_time']
    ordering = ['-check_in_time']
    readonly_fields = ['pass_number', 'check_in_time', 'created_at', 'updated_at']
