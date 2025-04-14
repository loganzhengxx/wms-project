from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts.views import UserViewSet, RoleViewSet, PermissionViewSet, RolePermissionViewSet, UserRoleViewSet, CustomAuthToken

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'roles', RoleViewSet)
router.register(r'permissions', PermissionViewSet)
router.register(r'role-permissions', RolePermissionViewSet)
router.register(r'user-roles', UserRoleViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('auth/register/', UserViewSet.as_view({'post': 'register'}), name='register'),
    path('auth/login/', UserViewSet.as_view({'post': 'login'}), name='login'),
    path('auth/me/', UserViewSet.as_view({'get': 'me'}), name='me'),
]
