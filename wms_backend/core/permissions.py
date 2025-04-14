from rest_framework import permissions

class IsTenantUser(permissions.BasePermission):
    """
    自定义权限，确保用户只能访问其所属租户的数据
    """
    
    def has_permission(self, request, view):
        # 确保用户已认证且属于当前租户
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # 确保对象属于用户的租户
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.user.tenant
        return False
