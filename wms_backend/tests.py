import unittest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Tenant
from accounts.models import User, Role, Permission
from warehouse.models import Warehouse, Area, Location
from inventory.models import Product, ProductCategory, Inventory, Batch
from reports.models import Report, Dashboard, KPI

User = get_user_model()

class MultiTenancyTestCase(TestCase):
    """测试多租户架构"""
    
    def setUp(self):
        # 创建测试租户
        self.tenant1 = Tenant.objects.create(name="测试租户1", domain_prefix="tenant1")
        self.tenant2 = Tenant.objects.create(name="测试租户2", domain_prefix="tenant2")
        
        # 创建测试用户
        self.user1 = User.objects.create_user(
            username="user1", 
            email="user1@example.com", 
            password="password123",
            tenant=self.tenant1
        )
        self.user2 = User.objects.create_user(
            username="user2", 
            email="user2@example.com", 
            password="password123",
            tenant=self.tenant2
        )
        
        # 创建测试数据
        self.category1 = ProductCategory.objects.create(
            name="类别1", 
            tenant=self.tenant1
        )
        self.category2 = ProductCategory.objects.create(
            name="类别2", 
            tenant=self.tenant2
        )
        
        self.product1 = Product.objects.create(
            name="产品1", 
            sku="SKU001", 
            category=self.category1,
            tenant=self.tenant1
        )
        self.product2 = Product.objects.create(
            name="产品2", 
            sku="SKU002", 
            category=self.category2,
            tenant=self.tenant2
        )
        
        # 创建API客户端
        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)
        self.client1.credentials(HTTP_X_TENANT_ID=str(self.tenant1.id))
        
        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)
        self.client2.credentials(HTTP_X_TENANT_ID=str(self.tenant2.id))
    
    def test_tenant_data_isolation(self):
        """测试租户数据隔离"""
        # 租户1只能看到自己的产品
        response = self.client1.get('/api/inventory/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], "产品1")
        
        # 租户2只能看到自己的产品
        response = self.client2.get('/api/inventory/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], "产品2")
    
    def test_cross_tenant_access_prevention(self):
        """测试跨租户访问防止"""
        # 租户1尝试访问租户2的产品
        response = self.client1.get(f'/api/inventory/products/{self.product2.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # 租户2尝试访问租户1的产品
        response = self.client2.get(f'/api/inventory/products/{self.product1.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class AuthenticationTestCase(TestCase):
    """测试用户认证和授权"""
    
    def setUp(self):
        # 创建测试租户
        self.tenant = Tenant.objects.create(name="测试租户", domain_prefix="test")
        
        # 创建角色和权限
        self.admin_role = Role.objects.create(
            name="管理员", 
            tenant=self.tenant
        )
        self.user_role = Role.objects.create(
            name="普通用户", 
            tenant=self.tenant
        )
        
        # 创建测试用户
        self.admin_user = User.objects.create_user(
            username="admin", 
            email="admin@example.com", 
            password="password123",
            tenant=self.tenant,
            is_staff=True
        )
        self.admin_user.roles.add(self.admin_role)
        
        self.normal_user = User.objects.create_user(
            username="user", 
            email="user@example.com", 
            password="password123",
            tenant=self.tenant
        )
        self.normal_user.roles.add(self.user_role)
        
        # 创建API客户端
        self.admin_client = APIClient()
        self.user_client = APIClient()
        self.anon_client = APIClient()
    
    def test_login_required(self):
        """测试需要登录的接口"""
        # 未登录用户无法访问API
        response = self.anon_client.get('/api/inventory/products/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 登录后可以访问API
        self.user_client.force_authenticate(user=self.normal_user)
        self.user_client.credentials(HTTP_X_TENANT_ID=str(self.tenant.id))
        response = self.user_client.get('/api/inventory/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_role_based_access_control(self):
        """测试基于角色的访问控制"""
        self.admin_client.force_authenticate(user=self.admin_user)
        self.admin_client.credentials(HTTP_X_TENANT_ID=str(self.tenant.id))
        
        self.user_client.force_authenticate(user=self.normal_user)
        self.user_client.credentials(HTTP_X_TENANT_ID=str(self.tenant.id))
        
        # 管理员可以访问用户管理API
        response = self.admin_client.get('/api/accounts/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 普通用户无法访问用户管理API
        response = self.user_client.get('/api/accounts/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class InventoryManagementTestCase(TestCase):
    """测试库存管理功能"""
    
    def setUp(self):
        # 创建测试租户
        self.tenant = Tenant.objects.create(name="测试租户", domain_prefix="test")
        
        # 创建测试用户
        self.user = User.objects.create_user(
            username="testuser", 
            email="test@example.com", 
            password="password123",
            tenant=self.tenant
        )
        
        # 创建测试数据
        self.category = ProductCategory.objects.create(
            name="测试类别", 
            tenant=self.tenant
        )
        
        self.product = Product.objects.create(
            name="测试产品", 
            sku="TST001", 
            category=self.category,
            cost_price=10.00,
            selling_price=20.00,
            min_stock_level=5,
            tenant=self.tenant
        )
        
        self.warehouse = Warehouse.objects.create(
            name="测试仓库", 
            code="WH001",
            tenant=self.tenant
        )
        
        self.area = Area.objects.create(
            name="测试区域", 
            code="A001",
            warehouse=self.warehouse,
            tenant=self.tenant
        )
        
        self.location = Location.objects.create(
            name="测试位置", 
            code="L001",
            area=self.area,
            warehouse=self.warehouse,
            tenant=self.tenant
        )
        
        self.batch = Batch.objects.create(
            product=self.product,
            batch_number="B001",
            expiry_date="2025-12-31",
            tenant=self.tenant
        )
        
        self.inventory = Inventory.objects.create(
            product=self.product,
            location=self.location,
            quantity=10,
            tenant=self.tenant
        )
        
        # 创建API客户端
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant.id))
    
    def test_product_management(self):
        """测试产品管理"""
        # 获取产品列表
        response = self.client.get('/api/inventory/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # 创建新产品
        new_product_data = {
            'name': '新产品',
            'sku': 'NEW001',
            'category': self.category.id,
            'cost_price': 15.00,
            'selling_price': 30.00
        }
        response = self.client.post('/api/inventory/products/', new_product_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证产品已创建
        response = self.client.get('/api/inventory/products/')
        self.assertEqual(len(response.data['results']), 2)
    
    def test_inventory_tracking(self):
        """测试库存跟踪"""
        # 获取库存列表
        response = self.client.get('/api/inventory/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['quantity'], 10)
        
        # 增加库存
        inventory_adjustment_data = {
            'inventory': self.inventory.id,
            'quantity': 5,
            'transaction_type': 'increase',
            'reference_type': 'manual_adjustment',
            'notes': '测试增加库存'
        }
        response = self.client.post('/api/inventory/transactions/', inventory_adjustment_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证库存已更新
        response = self.client.get(f'/api/inventory/inventory/{self.inventory.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 15)
    
    def test_batch_management(self):
        """测试批次管理"""
        # 获取批次列表
        response = self.client.get('/api/inventory/batches/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # 创建新批次
        new_batch_data = {
            'product': self.product.id,
            'batch_number': 'B002',
            'expiry_date': '2026-01-31'
        }
        response = self.client.post('/api/inventory/batches/', new_batch_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证批次已创建
        response = self.client.get('/api/inventory/batches/')
        self.assertEqual(len(response.data['results']), 2)

class ReportingAndAnalyticsTestCase(TestCase):
    """测试报表和分析功能"""
    
    def setUp(self):
        # 创建测试租户
        self.tenant = Tenant.objects.create(name="测试租户", domain_prefix="test")
        
        # 创建测试用户
        self.user = User.objects.create_user(
            username="testuser", 
            email="test@example.com", 
            password="password123",
            tenant=self.tenant
        )
        
        # 创建测试数据
        self.report = Report.objects.create(
            name="库存状态报表",
            report_type="inventory_status",
            created_by=self.user,
            tenant=self.tenant
        )
        
        self.dashboard = Dashboard.objects.create(
            name="库存仪表板",
            created_by=self.user,
            tenant=self.tenant
        )
        
        self.kpi = KPI.objects.create(
            name="库存周转率",
            category="inventory",
            calculation_method="计算方法...",
            target_value=5.0,
            tenant=self.tenant
        )
        
        # 创建API客户端
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant.id))
    
    def test_report_generation(self):
        """测试报表生成"""
        # 获取报表列表
        response = self.client.get('/api/reports/reports/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # 执行报表
        response = self.client.post(f'/api/reports/reports/{self.report.id}/execute/', {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
    
    def test_dashboard_management(self):
        """测试仪表板管理"""
        # 获取仪表板列表
        response = self.client.get('/api/reports/dashboards/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # 创建仪表板小部件
        widget_data = {
            'dashboard': self.dashboard.id,
            'title': '库存概览',
            'widget_type': 'chart',
            'data_source': 'inventory_summary',
            'position_x': 0,
            'position_y': 0,
            'width': 2,
            'height': 2
        }
        response = self.client.post('/api/reports/dashboard-widgets/', widget_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证小部件已创建
        response = self.client.get('/api/reports/dashboard-widgets/')
        self.assertEqual(len(response.data['results']), 1)
    
    def test_kpi_tracking(self):
        """测试KPI跟踪"""
        # 获取KPI列表
        response = self.client.get('/api/reports/kpis/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # 添加KPI值
        kpi_value_data = {
            'kpi': self.kpi.id,
            'date': '2025-04-14',
            'value': 4.5
        }
        response = self.client.post(f'/api/reports/kpis/{self.kpi.id}/add_value/', kpi_value_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证KPI值已添加
        response = self.client.get(f'/api/reports/kpis/{self.kpi.id}/values/')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['value'], 4.5)

if __name__ == '__main__':
    unittest.main()
