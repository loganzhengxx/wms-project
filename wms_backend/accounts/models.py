from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from core.models import Tenant, TenantAwareModel

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('用户必须有电子邮件地址')
        if not username:
            raise ValueError('用户必须有用户名')
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须设置is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须设置is_superuser=True')
        
        return self.create_user(email, username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    用户模型，继承Django的AbstractBaseUser和PermissionsMixin
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, verbose_name="租户")
    username = models.CharField(max_length=150, unique=True, verbose_name="用户名")
    email = models.EmailField(max_length=255, unique=True, verbose_name="电子邮件")
    first_name = models.CharField(max_length=30, blank=True, verbose_name="名")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="姓")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    is_staff = models.BooleanField(default=False, verbose_name="是否员工")
    is_admin = models.BooleanField(default=False, verbose_name="是否管理员")
    is_superuser = models.BooleanField(default=False, verbose_name="是否超级用户")
    date_joined = models.DateTimeField(default=timezone.now, verbose_name="加入日期")
    last_login = models.DateTimeField(null=True, blank=True, verbose_name="最后登录")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"
        db_table = "accounts_user"
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def get_short_name(self):
        return self.first_name or self.username

class Role(TenantAwareModel):
    """
    角色模型，用于角色基础的访问控制
    """
    name = models.CharField(max_length=100, verbose_name="角色名称")
    description = models.TextField(blank=True, verbose_name="角色描述")
    
    class Meta:
        verbose_name = "角色"
        verbose_name_plural = "角色"
        db_table = "accounts_role"
        unique_together = [['tenant', 'name']]
    
    def __str__(self):
        return self.name

class Permission(models.Model):
    """
    权限模型，定义系统中的权限
    """
    name = models.CharField(max_length=100, verbose_name="权限名称")
    codename = models.CharField(max_length=100, unique=True, verbose_name="权限代码")
    description = models.TextField(blank=True, verbose_name="权限描述")
    
    class Meta:
        verbose_name = "权限"
        verbose_name_plural = "权限"
        db_table = "accounts_permission"
    
    def __str__(self):
        return self.name

class RolePermission(models.Model):
    """
    角色权限关联模型
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="permissions", verbose_name="角色")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, verbose_name="权限")
    
    class Meta:
        verbose_name = "角色权限"
        verbose_name_plural = "角色权限"
        db_table = "accounts_role_permission"
        unique_together = [['role', 'permission']]
    
    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"

class UserRole(models.Model):
    """
    用户角色关联模型
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="roles", verbose_name="用户")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name="角色")
    
    class Meta:
        verbose_name = "用户角色"
        verbose_name_plural = "用户角色"
        db_table = "accounts_user_role"
        unique_together = [['user', 'role']]
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
