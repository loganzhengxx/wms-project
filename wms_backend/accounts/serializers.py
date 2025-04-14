from rest_framework import serializers
from accounts.models import User, Role, Permission, RolePermission, UserRole

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'tenant', 'username', 'email', 'first_name', 'last_name', 
                 'is_active', 'is_staff', 'is_admin', 'is_superuser', 
                 'date_joined', 'last_login', 'created_at', 'updated_at']
        read_only_fields = ['date_joined', 'last_login', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'description']

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'tenant', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class RolePermissionSerializer(serializers.ModelSerializer):
    permission_name = serializers.ReadOnlyField(source='permission.name')
    
    class Meta:
        model = RolePermission
        fields = ['id', 'role', 'permission', 'permission_name']

class UserRoleSerializer(serializers.ModelSerializer):
    role_name = serializers.ReadOnlyField(source='role.name')
    
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role', 'role_name']
