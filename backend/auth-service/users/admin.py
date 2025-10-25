"""
Admin configuration for users app
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PhotographerProfile, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'role', 'is_active', 'two_fa_enabled', 'created_at']
    list_filter = ['role', 'is_active', 'two_fa_enabled', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('role', 'phone', 'bio', 'profile_image', 'is_verified', 
                      'two_fa_enabled', 'two_fa_secret', 'last_login_ip')
        }),
    )


@admin.register(PhotographerProfile)
class PhotographerProfileAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'user', 'total_uploads', 'total_approved', 'created_at']
    search_fields = ['display_name', 'user__email']
    list_filter = ['created_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'target_type', 'target_id', 'created_at']
    list_filter = ['action', 'target_type', 'created_at']
    search_fields = ['user__email', 'target_type', 'target_id']
    readonly_fields = ['user', 'action', 'target_type', 'target_id', 'payload', 
                      'ip_address', 'user_agent', 'created_at']
