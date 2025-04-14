# WMS 智能库存系统架构文档

## 1. 系统概述

WMS 智能库存系统是一个基于现代Web技术的多租户仓库管理解决方案，旨在帮助企业高效管理库存、优化仓库操作流程、提高工作效率并降低成本。系统采用前后端分离架构，支持多种设备访问，并具备离线工作能力。

### 1.1 系统目标

- 提供全面的库存管理功能，包括产品管理、库存跟踪、批次管理等
- 支持多租户架构，确保不同组织的数据完全隔离
- 实现基于角色的权限控制，保障数据安全
- 提供强大的报表和分析功能，支持数据驱动决策
- 支持移动设备访问和离线工作，提高操作灵活性
- 确保系统可扩展性，支持业务增长和功能扩展

### 1.2 关键特性

- **多租户架构**：支持多个组织独立使用系统，数据完全隔离
- **用户管理**：基于角色的权限控制，确保数据安全
- **产品管理**：全面的产品信息管理，支持分类、属性和变体
- **仓库管理**：多仓库、多区域、多位置的层级结构
- **库存管理**：实时库存跟踪、批次管理和序列号追踪
- **入库管理**：采购订单、收货和上架流程
- **出库管理**：销售订单、拣货和发货流程
- **库存盘点**：周期盘点和实时调整
- **报表和分析**：全面的数据分析和可视化报表
- **移动支持**：响应式设计和PWA功能，支持移动设备使用
- **离线功能**：支持在网络不稳定环境下工作

## 2. 系统架构

### 2.1 总体架构

WMS 智能库存系统采用现代化的三层架构设计：

1. **表示层**：基于Vue.js和Quasar框架的前端应用，提供用户界面和交互
2. **业务逻辑层**：基于Django和Django REST Framework的后端服务，处理业务逻辑和数据访问
3. **数据存储层**：使用PostgreSQL数据库存储系统数据

系统架构图如下：

```
+----------------------------------+
|           客户端设备              |
| +------------------------------+ |
| |        浏览器 / PWA应用       | |
| +------------------------------+ |
+----------------------------------+
              |
              | HTTPS
              v
+----------------------------------+
|           负载均衡器              |
+----------------------------------+
              |
              v
+----------------------------------+
|           前端服务器              |
| +------------------------------+ |
| |      Quasar/Vue.js应用       | |
| +------------------------------+ |
+----------------------------------+
              |
              | REST API
              v
+----------------------------------+
|           应用服务器              |
| +------------------------------+ |
| |     Django应用 + DRF API     | |
| +------------------------------+ |
+----------------------------------+
              |
              v
+----------------------------------+
|           数据库服务器            |
| +------------------------------+ |
| |         PostgreSQL           | |
| +------------------------------+ |
+----------------------------------+
```

### 2.2 前端架构

前端采用基于Vue.js 3的Quasar框架，实现了PWA（渐进式Web应用）功能，支持响应式设计和离线工作模式。

#### 2.2.1 技术栈

- **Vue.js 3**：核心前端框架，采用组合式API
- **Quasar Framework**：UI组件库和PWA支持
- **Pinia**：状态管理
- **Vue Router**：客户端路由
- **Axios**：HTTP客户端
- **Workbox**：Service Worker和缓存管理

#### 2.2.2 前端模块结构

```
src/
├── assets/            # 静态资源
├── boot/              # 启动文件
├── components/        # 通用组件
├── css/               # 全局样式
├── layouts/           # 页面布局
├── pages/             # 页面组件
├── router/            # 路由配置
├── services/          # API服务
├── stores/            # 状态管理
└── utils/             # 工具函数
```

#### 2.2.3 离线功能实现

前端通过Service Worker实现离线功能，主要包括：

1. **资源缓存**：缓存静态资源、API响应和应用外壳
2. **离线数据存储**：使用IndexedDB存储离线操作数据
3. **后台同步**：在网络恢复时自动同步离线操作
4. **离线UI**：提供离线状态指示和降级UI

### 2.3 后端架构

后端采用Django框架和Django REST Framework，实现了RESTful API和多租户架构。

#### 2.3.1 技术栈

- **Django**：核心Web框架
- **Django REST Framework**：API开发框架
- **PostgreSQL**：关系型数据库
- **JWT**：认证机制
- **Celery**：异步任务处理（可选）
- **Redis**：缓存和消息队列（可选）

#### 2.3.2 后端模块结构

```
wms_backend/
├── core/               # 核心功能和多租户支持
├── accounts/           # 用户和权限管理
├── warehouse/          # 仓库和位置管理
├── inventory/          # 库存和产品管理
├── reports/            # 报表和分析功能
└── wms_backend/        # 项目配置
```

#### 2.3.3 多租户实现

系统采用基于共享数据库、独立Schema的多租户架构：

1. **租户识别**：通过请求头或子域名识别当前租户
2. **数据隔离**：所有模型继承自TenantAwareModel基类，自动添加租户过滤
3. **中间件**：TenantMiddleware负责解析租户信息并设置当前请求的租户上下文
4. **权限控制**：确保用户只能访问其所属租户的数据

### 2.4 数据库架构

系统使用PostgreSQL数据库，采用关系型数据模型设计。

#### 2.4.1 主要数据模型

```
+----------------+       +----------------+       +----------------+
|     Tenant     |------>|      User      |------>|      Role      |
+----------------+       +----------------+       +----------------+
        |                       |                        |
        |                       |                        |
        v                       v                        v
+----------------+       +----------------+       +----------------+
|    Product     |<------|   Inventory    |------>|   Location     |
+----------------+       +----------------+       +----------------+
        |                       |                        |
        |                       |                        |
        v                       v                        v
+----------------+       +----------------+       +----------------+
|     Batch      |<------|  Transaction   |------>|     Area       |
+----------------+       +----------------+       +----------------+
        |                       |                        |
        |                       |                        |
        v                       v                        v
+----------------+       +----------------+       +----------------+
| PurchaseOrder  |       |  SalesOrder    |       |   Warehouse    |
+----------------+       +----------------+       +----------------+
```

#### 2.4.2 关键数据模型说明

1. **Tenant**：租户模型，存储租户信息
2. **User**：用户模型，扩展Django内置用户模型
3. **Role**：角色模型，定义用户角色和权限
4. **Product**：产品模型，存储产品信息
5. **Inventory**：库存模型，关联产品和位置，记录库存数量
6. **Location**：位置模型，定义库存存放位置
7. **Warehouse**：仓库模型，最高级别的存储位置
8. **Area**：区域模型，仓库内的区域划分
9. **Batch**：批次模型，跟踪产品批次信息
10. **Transaction**：交易模型，记录库存变动
11. **PurchaseOrder**：采购订单模型，管理入库流程
12. **SalesOrder**：销售订单模型，管理出库流程

## 3. 系统组件

### 3.1 多租户组件

多租户组件负责租户识别、数据隔离和租户管理。

#### 3.1.1 租户中间件

```python
class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # 从请求头中获取租户ID
        tenant_id = request.headers.get('X-Tenant-ID')
        
        # 或从子域名中解析租户
        if not tenant_id:
            host = request.get_host().split(':')[0]
            subdomain = host.split('.')[0]
            if subdomain != settings.PRIMARY_DOMAIN:
                tenant = Tenant.objects.filter(domain_prefix=subdomain).first()
                if tenant:
                    tenant_id = tenant.id
        
        # 将租户ID存储在请求对象中
        request.tenant_id = tenant_id
        
        # 继续处理请求
        response = self.get_response(request)
        return response
```

#### 3.1.2 租户感知模型

```python
class TenantAwareModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
    class Meta:
        abstract = True
```

#### 3.1.3 租户过滤管理器

```python
class TenantAwareManager(models.Manager):
    def get_queryset(self):
        if hasattr(connection.get_thread_local(), 'tenant_id'):
            return super().get_queryset().filter(tenant_id=connection.get_thread_local().tenant_id)
        return super().get_queryset()
```

### 3.2 用户认证和授权组件

用户认证和授权组件负责用户身份验证、权限控制和访问管理。

#### 3.2.1 JWT认证

系统使用JWT（JSON Web Token）进行API认证：

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}
```

#### 3.2.2 基于角色的权限控制

```python
class Role(TenantAwareModel):
    name = models.CharField(max_length=100)
    permissions = models.ManyToManyField(Permission)
    
    def __str__(self):
        return self.name

class User(AbstractUser, TenantAwareModel):
    roles = models.ManyToManyField(Role)
    
    def has_permission(self, permission_codename):
        return self.is_superuser or self.roles.filter(
            permissions__codename=permission_codename
        ).exists()
```

#### 3.2.3 自定义权限检查

```python
class IsTenantUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.user.tenant
        return False
```

### 3.3 库存管理组件

库存管理组件负责产品、库存和批次的管理。

#### 3.3.1 产品管理

```python
class ProductCategory(TenantAwareModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    
    def __str__(self):
        return self.name

class Product(TenantAwareModel):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_stock_level = models.IntegerField(default=0)
    max_stock_level = models.IntegerField(null=True, blank=True)
    attributes = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    @property
    def current_stock(self):
        return self.inventory_set.aggregate(total=Sum('quantity'))['total'] or 0
```

#### 3.3.2 库存跟踪

```python
class Inventory(TenantAwareModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey('warehouse.Location', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)
    last_counted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('product', 'location', 'tenant')
    
    def __str__(self):
        return f"{self.product.name} @ {self.location.name}: {self.quantity}"
    
    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity
```

#### 3.3.3 批次管理

```python
class Batch(TenantAwareModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    batch_number = models.CharField(max_length=50)
    production_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('product', 'batch_number', 'tenant')
    
    def __str__(self):
        return f"{self.product.name} - {self.batch_number}"
    
    @property
    def quantity(self):
        return self.batchinventory_set.aggregate(total=Sum('quantity'))['total'] or 0
```

### 3.4 仓库管理组件

仓库管理组件负责仓库、区域、位置和任务的管理。

#### 3.4.1 仓库结构

```python
class Warehouse(TenantAwareModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    address = models.TextField()
    contact_person = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Area(TenantAwareModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('code', 'warehouse', 'tenant')
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Location(TenantAwareModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    capacity = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('code', 'warehouse', 'tenant')
    
    def __str__(self):
        return f"{self.name} ({self.code})"
```

#### 3.4.2 任务管理

```python
class Task(TenantAwareModel):
    TASK_TYPES = (
        ('receiving', '收货'),
        ('putaway', '上架'),
        ('picking', '拣货'),
        ('packing', '打包'),
        ('shipping', '发货'),
        ('counting', '盘点'),
        ('movement', '移动'),
    )
    
    STATUS_CHOICES = (
        ('pending', '待处理'),
        ('assigned', '已分配'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    )
    
    PRIORITY_CHOICES = (
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
    )
    
    task_number = models.CharField(max_length=20, unique=True)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.CharField(max_length=50, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey('accounts.User', related_name='created_tasks', on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.task_number} ({self.get_task_type_display()})"
    
    def save(self, *args, **kwargs):
        if not self.task_number:
            # 生成任务编号
            prefix = 'TASK'
            date_str = datetime.now().strftime('%Y%m')
            last_task = Task.objects.filter(
                task_number__startswith=f"{prefix}-{date_str}"
            ).order_by('task_number').last()
            
            if last_task:
                last_num = int(last_task.task_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
                
            self.task_number = f"{prefix}-{date_str}-{new_num:03d}"
            
        super().save(*args, **kwargs)
```

### 3.5 报表和分析组件

报表和分析组件负责数据分析、报表生成和可视化。

#### 3.5.1 报表定义

```python
class Report(TenantAwareModel):
    REPORT_TYPES = (
        ('inventory_status', '库存状态'),
        ('inventory_movement', '库存移动'),
        ('sales_analysis', '销售分析'),
        ('purchase_analysis', '采购分析'),
        ('warehouse_performance', '仓库绩效'),
        ('custom', '自定义报表'),
    )
    
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return self.name
    
    def execute(self, parameters=None, format='json'):
        # 根据报表类型执行不同的报表逻辑
        if self.report_type == 'inventory_status':
            return self._execute_inventory_status(parameters)
        elif self.report_type == 'inventory_movement':
            return self._execute_inventory_movement(parameters)
        # ... 其他报表类型
        
    def _execute_inventory_status(self, parameters):
        # 实现库存状态报表逻辑
        warehouse_id = parameters.get('warehouse')
        product_category = parameters.get('category')
        
        query = Inventory.objects.filter(tenant=self.tenant)
        
        if warehouse_id:
            query = query.filter(location__warehouse_id=warehouse_id)
            
        if product_category:
            query = query.filter(product__category_id=product_category)
            
        # 聚合计算
        summary = {
            'total_products': query.values('product').distinct().count(),
            'total_quantity': query.aggregate(total=Sum('quantity'))['total'] or 0,
            'total_value': query.annotate(
                value=F('quantity') * F('product__cost_price')
            ).aggregate(total=Sum('value'))['total'] or 0,
            'low_stock_items': query.filter(
                quantity__lt=F('product__min_stock_level')
            ).count(),
        }
        
        # 详细数据
        details = []
        for inv in query:
            details.append({
                'product': {
                    'id': inv.product.id,
                    'name': inv.product.name,
                    'sku': inv.product.sku,
                },
                'quantity': inv.quantity,
                'value': inv.quantity * inv.product.cost_price,
                'status': 'low' if inv.quantity < inv.product.min_stock_level else 'normal',
            })
            
        return {
            'summary': summary,
            'details': details,
        }
```

#### 3.5.2 仪表板

```python
class Dashboard(TenantAwareModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return self.name

class DashboardWidget(TenantAwareModel):
    WIDGET_TYPES = (
        ('chart', '图表'),
        ('table', '表格'),
        ('metric', '指标'),
        ('list', '列表'),
    )
    
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widgets')
    title = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    data_source = models.CharField(max_length=50)
    parameters = models.JSONField(default=dict, blank=True)
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    width = models.IntegerField(default=1)
    height = models.IntegerField(default=1)
    
    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"
    
    def get_data(self):
        # 根据数据源获取数据
        if self.data_source == 'inventory_summary':
            return self._get_inventory_summary()
        # ... 其他数据源
        
    def _get_inventory_summary(self):
        # 实现库存概览数据逻辑
        return {
            'labels': ['产品A', '产品B', '产品C', '产品D', '产品E'],
            'datasets': [
                {
                    'label': '库存数量',
                    'data': [45, 30, 25, 15, 10],
                }
            ]
        }
```

#### 3.5.3 KPI跟踪

```python
class KPI(TenantAwareModel):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    calculation_method = models.TextField(blank=True)
    unit = models.CharField(max_length=20, blank=True)
    target_value = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    @property
    def current_value(self):
        latest = self.kpivalue_set.order_by('-date').first()
        return latest.value if latest else None
    
    @property
    def status(self):
        if self.current_value is None or self.target_value is None:
            return 'unknown'
        
        ratio = self.current_value / self.target_value
        if ratio >= 0.95:
            return 'good'
        elif ratio >= 0.8:
            return 'warning'
        else:
            return 'critical'

class KPIValue(TenantAwareModel):
    kpi = models.ForeignKey(KPI, on_delete=models.CASCADE)
    date = models.DateField()
    value = models.FloatField()
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('kpi', 'date', 'tenant')
    
    def __str__(self):
        return f"{self.kpi.name}: {self.value} ({self.date})"
```

### 3.6 离线功能组件

离线功能组件负责实现PWA功能和离线数据同步。

#### 3.6.1 Service Worker

```javascript
// src-pwa/custom-service-worker.js

import { precacheAndRoute } from 'workbox-precaching'
import { registerRoute } from 'workbox-routing'
import { StaleWhileRevalidate, CacheFirst, NetworkFirst } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'
import { CacheableResponsePlugin } from 'workbox-cacheable-response'

// 预缓存应用外壳
precacheAndRoute(self.__WB_MANIFEST)

// 缓存API请求
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({
    cacheName: 'api-cache',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 60 * 60 * 24 // 1天
      })
    ]
  })
)

// 缓存静态资源
registerRoute(
  ({ request }) => request.destination === 'style' || 
                   request.destination === 'script' || 
                   request.destination === 'font',
  new CacheFirst({
    cacheName: 'static-resources',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: 60,
        maxAgeSeconds: 60 * 60 * 24 * 30 // 30天
      })
    ]
  })
)

// 后台同步
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-inventory-transactions') {
    event.waitUntil(syncInventoryTransactions())
  }
})

// 同步库存交易
async function syncInventoryTransactions() {
  try {
    const db = await openDB('wms-offline-db', 1)
    const tx = db.transaction('pending-transactions', 'readwrite')
    const store = tx.objectStore('pending-transactions')
    
    const pendingTransactions = await store.getAll()
    
    for (const transaction of pendingTransactions) {
      try {
        const response = await fetch('/api/inventory/transactions/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(transaction)
        })
        
        if (response.ok) {
          await store.delete(transaction.id)
        }
      } catch (error) {
        console.error('Failed to sync transaction:', error)
      }
    }
    
    await tx.complete
  } catch (error) {
    console.error('Error during sync:', error)
  }
}
```

#### 3.6.2 离线数据存储

```javascript
// src/services/offline-store.js

import { openDB } from 'idb'

const DB_NAME = 'wms-offline-db'
const DB_VERSION = 1

// 初始化IndexedDB
export async function initDB() {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      // 创建存储库存交易的对象存储
      if (!db.objectStoreNames.contains('pending-transactions')) {
        db.createObjectStore('pending-transactions', { keyPath: 'id' })
      }
      
      // 创建缓存产品数据的对象存储
      if (!db.objectStoreNames.contains('products')) {
        const productStore = db.createObjectStore('products', { keyPath: 'id' })
        productStore.createIndex('sku', 'sku', { unique: true })
      }
      
      // 创建缓存库存数据的对象存储
      if (!db.objectStoreNames.contains('inventory')) {
        const inventoryStore = db.createObjectStore('inventory', { keyPath: 'id' })
        inventoryStore.createIndex('product_id', 'product.id', { unique: false })
        inventoryStore.createIndex('location_id', 'location.id', { unique: false })
      }
    }
  })
}

// 保存离线交易
export async function saveOfflineTransaction(transaction) {
  const db = await initDB()
  transaction.id = Date.now().toString()
  transaction.created_at = new Date().toISOString()
  transaction.synced = false
  
  await db.add('pending-transactions', transaction)
  
  // 注册后台同步
  if ('serviceWorker' in navigator && 'SyncManager' in window) {
    const registration = await navigator.serviceWorker.ready
    await registration.sync.register('sync-inventory-transactions')
  }
  
  return transaction
}

// 缓存产品数据
export async function cacheProducts(products) {
  const db = await initDB()
  const tx = db.transaction('products', 'readwrite')
  
  for (const product of products) {
    await tx.store.put(product)
  }
  
  await tx.complete
}

// 获取缓存的产品数据
export async function getCachedProducts() {
  const db = await initDB()
  return db.getAll('products')
}

// 缓存库存数据
export async function cacheInventory(inventoryItems) {
  const db = await initDB()
  const tx = db.transaction('inventory', 'readwrite')
  
  for (const item of inventoryItems) {
    await tx.store.put(item)
  }
  
  await tx.complete
}

// 获取缓存的库存数据
export async function getCachedInventory(productId = null) {
  const db = await initDB()
  
  if (productId) {
    return db.getAllFromIndex('inventory', 'product_id', productId)
  }
  
  return db.getAll('inventory')
}
```

## 4. 接口设计

系统采用RESTful API设计，主要接口分为以下几类：

### 4.1 认证接口

- `POST /api/auth/token/`: 获取访问令牌
- `POST /api/auth/token/refresh/`: 刷新访问令牌
- `POST /api/auth/token/verify/`: 验证令牌有效性

### 4.2 用户管理接口

- `GET /api/accounts/users/`: 获取用户列表
- `POST /api/accounts/users/`: 创建用户
- `GET /api/accounts/users/{id}/`: 获取用户详情
- `PUT /api/accounts/users/{id}/`: 更新用户
- `DELETE /api/accounts/users/{id}/`: 删除用户

### 4.3 产品管理接口

- `GET /api/inventory/categories/`: 获取产品分类列表
- `POST /api/inventory/categories/`: 创建产品分类
- `GET /api/inventory/products/`: 获取产品列表
- `POST /api/inventory/products/`: 创建产品
- `GET /api/inventory/products/{id}/`: 获取产品详情
- `PUT /api/inventory/products/{id}/`: 更新产品
- `DELETE /api/inventory/products/{id}/`: 删除产品

### 4.4 仓库管理接口

- `GET /api/warehouse/warehouses/`: 获取仓库列表
- `POST /api/warehouse/warehouses/`: 创建仓库
- `GET /api/warehouse/areas/`: 获取区域列表
- `POST /api/warehouse/areas/`: 创建区域
- `GET /api/warehouse/locations/`: 获取位置列表
- `POST /api/warehouse/locations/`: 创建位置

### 4.5 库存管理接口

- `GET /api/inventory/inventory/`: 获取库存列表
- `POST /api/inventory/transactions/`: 创建库存交易
- `POST /api/inventory/movements/`: 创建库存移动
- `GET /api/inventory/batches/`: 获取批次列表
- `POST /api/inventory/batches/`: 创建批次

### 4.6 入库管理接口

- `GET /api/inventory/purchase-orders/`: 获取采购订单列表
- `POST /api/inventory/purchase-orders/`: 创建采购订单
- `GET /api/inventory/purchase-orders/{id}/`: 获取采购订单详情
- `PUT /api/inventory/purchase-orders/{id}/`: 更新采购订单
- `POST /api/inventory/purchase-orders/{id}/receive/`: 接收采购订单

### 4.7 出库管理接口

- `GET /api/inventory/sales-orders/`: 获取销售订单列表
- `POST /api/inventory/sales-orders/`: 创建销售订单
- `GET /api/inventory/sales-orders/{id}/`: 获取销售订单详情
- `PUT /api/inventory/sales-orders/{id}/`: 更新销售订单
- `POST /api/inventory/sales-orders/{id}/ship/`: 发货销售订单

### 4.8 报表和分析接口

- `GET /api/reports/reports/`: 获取报表列表
- `POST /api/reports/reports/{id}/execute/`: 执行报表
- `GET /api/reports/dashboards/`: 获取仪表板列表
- `GET /api/reports/kpis/`: 获取KPI列表
- `POST /api/reports/kpis/{id}/add_value/`: 添加KPI值

## 5. 安全设计

### 5.1 认证和授权

系统采用多层次的安全机制：

1. **JWT认证**：所有API请求需要携带有效的JWT令牌
2. **租户隔离**：确保用户只能访问其所属租户的数据
3. **基于角色的权限控制**：根据用户角色限制功能访问
4. **对象级权限**：验证用户对特定对象的操作权限

### 5.2 数据安全

1. **HTTPS传输**：所有API通信使用HTTPS加密
2. **密码加密**：用户密码使用bcrypt算法加密存储
3. **输入验证**：所有用户输入经过严格验证，防止注入攻击
4. **CSRF保护**：实施跨站请求伪造保护
5. **XSS防护**：前端实施内容安全策略，防止跨站脚本攻击

### 5.3 审计日志

系统记录关键操作的审计日志：

```python
class AuditLog(TenantAwareModel):
    ACTION_TYPES = (
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
        ('login', '登录'),
        ('logout', '登出'),
        ('other', '其他'),
    )
    
    user = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_action_display()} {self.entity_type} by {self.user}"
```

## 6. 性能优化

### 6.1 数据库优化

1. **索引优化**：为常用查询字段创建索引
2. **查询优化**：使用select_related和prefetch_related减少数据库查询
3. **分页**：所有列表API实施分页，避免大量数据传输
4. **数据库连接池**：使用连接池管理数据库连接

### 6.2 缓存策略

1. **Redis缓存**：使用Redis缓存频繁访问的数据
2. **查询缓存**：缓存复杂查询结果
3. **前端缓存**：使用Service Worker缓存静态资源和API响应

### 6.3 异步处理

1. **Celery任务队列**：将耗时操作放入异步任务队列
2. **后台处理**：报表生成等耗时操作在后台处理
3. **批量操作**：支持批量导入导出，减少请求次数

## 7. 扩展性设计

### 7.1 水平扩展

系统设计支持水平扩展：

1. **无状态API**：后端API无状态，可部署多个实例
2. **负载均衡**：使用负载均衡器分发请求
3. **数据库读写分离**：支持主从复制，分离读写操作

### 7.2 模块化设计

系统采用模块化设计，便于功能扩展：

1. **插件架构**：核心功能和扩展功能分离
2. **事件系统**：通过事件机制实现模块间通信
3. **API版本控制**：支持API版本演进

### 7.3 自定义扩展

系统支持多种自定义扩展：

1. **自定义字段**：产品和库存支持自定义属性
2. **自定义报表**：用户可创建自定义报表
3. **自定义工作流**：支持自定义业务流程

## 8. 部署架构

### 8.1 开发环境

```
+----------------------------------+
|           开发者工作站            |
| +------------------------------+ |
| |     前端开发服务器 (npm)      | |
| +------------------------------+ |
| |     后端开发服务器 (Django)   | |
| +------------------------------+ |
| |     本地数据库 (PostgreSQL)   | |
| +------------------------------+ |
+----------------------------------+
```

### 8.2 测试环境

```
+----------------------------------+
|           测试服务器              |
| +------------------------------+ |
| |     前端应用 (Nginx)          | |
| +------------------------------+ |
| |     后端API (Gunicorn)       | |
| +------------------------------+ |
| |     数据库 (PostgreSQL)       | |
| +------------------------------+ |
+----------------------------------+
```

### 8.3 生产环境

```
+----------------------------------+
|           负载均衡器              |
+----------------------------------+
            /        \
           /          \
+----------------+  +----------------+
|  前端服务器1    |  |  前端服务器2    |
|  (Nginx)      |  |  (Nginx)      |
+----------------+  +----------------+
            \        /
             \      /
+----------------------------------+
|           API网关                |
+----------------------------------+
            /        \
           /          \
+----------------+  +----------------+
|  应用服务器1    |  |  应用服务器2    |
|  (Gunicorn)    |  |  (Gunicorn)    |
+----------------+  +----------------+
            \        /
             \      /
+----------------------------------+
|           数据库集群              |
|  (PostgreSQL主从复制)            |
+----------------------------------+
            |
+----------------------------------+
|           缓存服务器              |
|           (Redis)               |
+----------------------------------+
```

## 9. 监控和运维

### 9.1 日志管理

系统实施全面的日志管理：

1. **应用日志**：记录应用运行状态和错误
2. **访问日志**：记录API访问情况
3. **审计日志**：记录用户操作
4. **性能日志**：记录性能指标

### 9.2 监控系统

推荐使用以下监控工具：

1. **Prometheus**：收集性能指标
2. **Grafana**：可视化监控数据
3. **Sentry**：错误跟踪和报告
4. **ELK Stack**：日志聚合和分析

### 9.3 备份策略

实施多层次备份策略：

1. **数据库备份**：每日全量备份，每小时增量备份
2. **文件备份**：定期备份上传文件
3. **配置备份**：备份系统配置
4. **异地备份**：关键数据异地备份

## 10. 未来扩展

系统设计考虑了以下未来扩展方向：

1. **移动应用**：开发原生移动应用，提供更好的移动体验
2. **物联网集成**：集成RFID、条码扫描器等设备
3. **人工智能**：引入AI进行库存预测和优化
4. **区块链**：使用区块链技术增强供应链透明度
5. **多语言支持**：增加多语言界面
6. **第三方集成**：集成ERP、CRM等系统

## 11. 总结

WMS 智能库存系统采用现代化的技术栈和架构设计，实现了全面的库存管理功能，支持多租户、移动访问和离线工作。系统具有良好的可扩展性、安全性和性能，能够满足不同规模企业的库存管理需求。

通过模块化设计和标准化接口，系统可以灵活扩展和集成，适应未来业务发展和技术演进。
