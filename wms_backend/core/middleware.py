from django.middleware.common import CommonMiddleware
from threading import local

# 创建线程本地存储，用于存储当前租户信息
_thread_locals = local()

def get_current_tenant():
    """
    获取当前请求的租户ID
    """
    return getattr(_thread_locals, 'tenant_id', None)

def set_current_tenant(tenant_id):
    """
    设置当前请求的租户ID
    """
    _thread_locals.tenant_id = tenant_id

class TenantMiddleware:
    """
    租户中间件，用于识别当前请求的租户
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # 从请求头中获取租户ID
        tenant_id = request.headers.get('X-Tenant-ID')
        
        # 将租户ID存储在请求对象中，以便后续使用
        request.tenant_id = tenant_id
        
        # 将租户ID存储在线程本地变量中，以便在视图和模型中使用
        set_current_tenant(tenant_id)
        
        # 继续处理请求
        response = self.get_response(request)
        return response
