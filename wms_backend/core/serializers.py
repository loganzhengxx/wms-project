from rest_framework import serializers
from core.models import Tenant, Setting, Notification, AuditLog

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'subdomain', 'created_at', 'updated_at', 'is_active', 'settings']
        read_only_fields = ['created_at', 'updated_at']

class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = ['id', 'tenant', 'group', 'key', 'value', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'tenant', 'user_id', 'title', 'message', 'notification_type', 
                 'is_read', 'reference_type', 'reference_id', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'tenant', 'user_id', 'action', 'entity_type', 'entity_id', 
                 'old_values', 'new_values', 'ip_address', 'user_agent', 'created_at']
        read_only_fields = ['created_at']
