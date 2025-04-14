from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from core.models import Tenant, Setting, Notification, AuditLog
from core.serializers import TenantSerializer, SettingSerializer, NotificationSerializer, AuditLogSerializer
from core.middleware import get_current_tenant

class TenantViewSet(viewsets.ModelViewSet):
    """
    租户管理视图集
    """
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        # 超级用户可以看到所有租户，普通用户只能看到自己的租户
        if self.request.user.is_superuser:
            return Tenant.objects.all()
        return Tenant.objects.filter(id=self.request.user.tenant_id)

class SettingViewSet(viewsets.ModelViewSet):
    """
    设置管理视图集
    """
    queryset = Setting.objects.all()
    serializer_class = SettingSerializer
    
    def get_queryset(self):
        tenant = get_current_tenant()
        # 返回系统设置和当前租户的设置
        return Setting.objects.filter(tenant=tenant) | Setting.objects.filter(tenant=None)
    
    def perform_create(self, serializer):
        tenant = get_current_tenant()
        serializer.save(tenant=tenant)

class NotificationViewSet(viewsets.ModelViewSet):
    """
    通知管理视图集
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        tenant = get_current_tenant()
        return Notification.objects.filter(tenant=tenant, user_id=self.request.user.id)
    
    def perform_create(self, serializer):
        tenant = get_current_tenant()
        serializer.save(tenant=tenant)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        tenant = get_current_tenant()
        Notification.objects.filter(tenant=tenant, user_id=request.user.id, is_read=False).update(is_read=True)
        return Response({'status': 'all notifications marked as read'})

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    审计日志视图集（只读）
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        tenant = get_current_tenant()
        return AuditLog.objects.filter(tenant=tenant)
