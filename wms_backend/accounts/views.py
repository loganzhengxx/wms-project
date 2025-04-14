from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import authenticate
from accounts.models import User, Role, Permission, RolePermission, UserRole
from accounts.serializers import UserSerializer, RoleSerializer, PermissionSerializer, RolePermissionSerializer, UserRoleSerializer
from core.middleware import get_current_tenant

class CustomAuthToken(ObtainAuthToken):
    """
    自定义令牌获取视图，返回用户信息和令牌
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'username': user.username,
            'is_staff': user.is_staff,
            'is_admin': user.is_admin,
            'tenant_id': user.tenant_id
        })

class UserViewSet(viewsets.ModelViewSet):
    """
    用户管理视图集
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_queryset(self):
        tenant = get_current_tenant()
        # 超级用户可以看到所有用户，管理员可以看到自己租户的所有用户，普通用户只能看到自己
        if self.request.user.is_superuser:
            return User.objects.all()
        elif self.request.user.is_admin:
            return User.objects.filter(tenant=tenant)
        return User.objects.filter(id=self.request.user.id)
    
    def perform_create(self, serializer):
        tenant = get_current_tenant()
        serializer.save(tenant=tenant)
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        用户注册接口
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        用户登录接口
        """
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({'error': '请提供邮箱和密码'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(email=email, password=password)
        
        if not user:
            return Response({'error': '无效的凭据'}, status=status.HTTP_401_UNAUTHORIZED)
        
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'username': user.username,
            'is_staff': user.is_staff,
            'is_admin': user.is_admin,
            'tenant_id': user.tenant_id
        })
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        获取当前用户信息
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class RoleViewSet(viewsets.ModelViewSet):
    """
    角色管理视图集
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    
    def get_queryset(self):
        tenant = get_current_tenant()
        return Role.objects.filter(tenant=tenant)
    
    def perform_create(self, serializer):
        tenant = get_current_tenant()
        serializer.save(tenant=tenant)

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    权限视图集（只读）
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer

class RolePermissionViewSet(viewsets.ModelViewSet):
    """
    角色权限关联视图集
    """
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    
    def get_queryset(self):
        tenant = get_current_tenant()
        return RolePermission.objects.filter(role__tenant=tenant)

class UserRoleViewSet(viewsets.ModelViewSet):
    """
    用户角色关联视图集
    """
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    
    def get_queryset(self):
        tenant = get_current_tenant()
        if self.request.user.is_admin:
            return UserRole.objects.filter(user__tenant=tenant)
        return UserRole.objects.filter(user=self.request.user)
