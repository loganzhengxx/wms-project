from django.db import models

class Tenant(models.Model):
    """租户模型"""
    name = models.CharField(max_length=100, verbose_name="租户名称")
    domain_prefix = models.CharField(max_length=50, unique=True, verbose_name="域名前缀")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "租户"
        verbose_name_plural = "租户"
        ordering = ['name']

class TenantAwareModel(models.Model):
    """租户感知模型基类"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="租户")
    
    class Meta:
        abstract = True
