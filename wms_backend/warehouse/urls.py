from django.urls import path, include
from rest_framework.routers import DefaultRouter
from warehouse.views import WarehouseViewSet, ZoneViewSet, LocationViewSet, TaskViewSet, TaskHistoryViewSet

router = DefaultRouter()
router.register(r'warehouses', WarehouseViewSet)
router.register(r'zones', ZoneViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'task-history', TaskHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('tasks/<int:pk>/assign/', TaskViewSet.as_view({'post': 'assign'}), name='task-assign'),
    path('tasks/<int:pk>/start/', TaskViewSet.as_view({'post': 'start'}), name='task-start'),
    path('tasks/<int:pk>/complete/', TaskViewSet.as_view({'post': 'complete'}), name='task-complete'),
    path('tasks/<int:pk>/cancel/', TaskViewSet.as_view({'post': 'cancel'}), name='task-cancel'),
]
