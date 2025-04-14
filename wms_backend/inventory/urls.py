from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'categories', views.ProductCategoryViewSet)
router.register(r'attributes', views.ProductAttributeViewSet)
router.register(r'batches', views.BatchViewSet)
router.register(r'serial-numbers', views.SerialNumberViewSet)
router.register(r'inventory', views.InventoryViewSet)
router.register(r'inventory-counts', views.InventoryCountViewSet)
router.register(r'inventory-count-items', views.InventoryCountItemViewSet)
router.register(r'inventory-alerts', views.InventoryAlertViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
