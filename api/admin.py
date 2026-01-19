from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Installer, Installation, Document, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role',)}),
    )


@admin.register(Installer)
class InstallerAdmin(admin.ModelAdmin):
    list_display = ['company', 'name', 'email', 'phone', 'created_at']
    list_filter = ['coverage', 'created_at']
    search_fields = ['company', 'name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    
    def email(self, obj):
        return obj.user.email


@admin.register(Installation)
class InstallationAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'status', 'assigned_installer', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer_name', 'customer_email', 'address']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'installation', 'document_type', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'action', 'model_name', 'object_id', 'created_at']
    list_filter = ['action', 'model_name', 'created_at']
    readonly_fields = ['created_at']
