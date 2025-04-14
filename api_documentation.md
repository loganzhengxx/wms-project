# WMS 智能库存系统 API 文档

## 概述

本文档详细描述了 WMS 智能库存系统的 RESTful API 接口。所有 API 遵循 REST 设计原则，使用 JSON 作为数据交换格式，并使用标准 HTTP 方法和状态码。

## 基础信息

- **基础 URL**: `https://your-domain.com/api/`
- **认证方式**: JWT (JSON Web Token)
- **内容类型**: `application/json`

## 认证

### 获取令牌

```
POST /auth/token/
```

获取用户访问令牌。

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

**响应**:

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "roles": ["admin"]
  }
}
```

### 刷新令牌

```
POST /auth/token/refresh/
```

使用刷新令牌获取新的访问令牌。

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| refresh | string | 是 | 刷新令牌 |

**响应**:

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 验证令牌

```
POST /auth/token/verify/
```

验证访问令牌是否有效。

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| token | string | 是 | 访问令牌 |

**响应**:

如果令牌有效，返回 HTTP 200 状态码和空对象。如果无效，返回 HTTP 401 状态码和错误信息。

## 多租户

### 获取当前租户

```
GET /core/tenant/
```

获取当前用户所属的租户信息。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID (可选) |

**响应**:

```json
{
  "id": 1,
  "name": "示例公司",
  "domain_prefix": "example",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

## 用户管理

### 获取用户列表

```
GET /accounts/users/
```

获取当前租户下的所有用户。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为 1 |
| page_size | integer | 否 | 每页记录数，默认为 10 |
| search | string | 否 | 搜索关键词 |
| role | string | 否 | 按角色筛选 |

**响应**:

```json
{
  "count": 100,
  "next": "https://your-domain.com/api/accounts/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "first_name": "Admin",
      "last_name": "User",
      "is_active": true,
      "roles": [
        {
          "id": 1,
          "name": "管理员"
        }
      ],
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    // 更多用户...
  ]
}
```

### 创建用户

```
POST /accounts/users/
```

在当前租户下创建新用户。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**请求体**:

```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "securepassword",
  "first_name": "New",
  "last_name": "User",
  "roles": [2]
}
```

**响应**:

```json
{
  "id": 2,
  "username": "newuser",
  "email": "newuser@example.com",
  "first_name": "New",
  "last_name": "User",
  "is_active": true,
  "roles": [
    {
      "id": 2,
      "name": "库存专员"
    }
  ],
  "created_at": "2025-04-14T03:30:00Z",
  "updated_at": "2025-04-14T03:30:00Z"
}
```

### 获取用户详情

```
GET /accounts/users/{id}/
```

获取指定用户的详细信息。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**响应**:

```json
{
  "id": 2,
  "username": "newuser",
  "email": "newuser@example.com",
  "first_name": "New",
  "last_name": "User",
  "is_active": true,
  "roles": [
    {
      "id": 2,
      "name": "库存专员"
    }
  ],
  "permissions": [
    "view_inventory",
    "add_inventory",
    "change_inventory"
  ],
  "created_at": "2025-04-14T03:30:00Z",
  "updated_at": "2025-04-14T03:30:00Z"
}
```

### 更新用户

```
PUT /accounts/users/{id}/
```

更新指定用户的信息。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**请求体**:

```json
{
  "email": "updated@example.com",
  "first_name": "Updated",
  "last_name": "User",
  "roles": [2, 3]
}
```

**响应**:

```json
{
  "id": 2,
  "username": "newuser",
  "email": "updated@example.com",
  "first_name": "Updated",
  "last_name": "User",
  "is_active": true,
  "roles": [
    {
      "id": 2,
      "name": "库存专员"
    },
    {
      "id": 3,
      "name": "仓库经理"
    }
  ],
  "created_at": "2025-04-14T03:30:00Z",
  "updated_at": "2025-04-14T03:35:00Z"
}
```

### 删除用户

```
DELETE /accounts/users/{id}/
```

删除指定用户。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**响应**:

成功删除返回 HTTP 204 状态码，无响应体。

## 产品管理

### 获取产品分类列表

```
GET /inventory/categories/
```

获取产品分类列表。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为 1 |
| page_size | integer | 否 | 每页记录数，默认为 10 |
| parent | integer | 否 | 父分类 ID |

**响应**:

```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "电子产品",
      "description": "各类电子设备",
      "parent": null,
      "children": [
        {
          "id": 2,
          "name": "手机",
          "description": "智能手机和配件"
        },
        {
          "id": 3,
          "name": "电脑",
          "description": "笔记本和台式电脑"
        }
      ],
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    // 更多分类...
  ]
}
```

### 创建产品分类

```
POST /inventory/categories/
```

创建新的产品分类。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**请求体**:

```json
{
  "name": "办公用品",
  "description": "各类办公用品和文具",
  "parent": null
}
```

**响应**:

```json
{
  "id": 4,
  "name": "办公用品",
  "description": "各类办公用品和文具",
  "parent": null,
  "children": [],
  "created_at": "2025-04-14T03:40:00Z",
  "updated_at": "2025-04-14T03:40:00Z"
}
```

### 获取产品列表

```
GET /inventory/products/
```

获取产品列表。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为 1 |
| page_size | integer | 否 | 每页记录数，默认为 10 |
| search | string | 否 | 搜索关键词 |
| category | integer | 否 | 分类 ID |
| min_stock | integer | 否 | 最小库存量 |
| max_stock | integer | 否 | 最大库存量 |

**响应**:

```json
{
  "count": 100,
  "next": "https://your-domain.com/api/inventory/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "iPhone 13",
      "sku": "IP13-128-BLK",
      "description": "iPhone 13 128GB 黑色",
      "category": {
        "id": 2,
        "name": "手机"
      },
      "cost_price": 5000.00,
      "selling_price": 6999.00,
      "min_stock_level": 10,
      "max_stock_level": 100,
      "current_stock": 45,
      "attributes": {
        "color": "黑色",
        "storage": "128GB"
      },
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    // 更多产品...
  ]
}
```

### 创建产品

```
POST /inventory/products/
```

创建新产品。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**请求体**:

```json
{
  "name": "MacBook Pro",
  "sku": "MBP-M2-16-512",
  "description": "MacBook Pro M2 16GB 512GB",
  "category": 3,
  "cost_price": 8000.00,
  "selling_price": 9999.00,
  "min_stock_level": 5,
  "max_stock_level": 50,
  "attributes": {
    "processor": "M2",
    "ram": "16GB",
    "storage": "512GB"
  }
}
```

**响应**:

```json
{
  "id": 2,
  "name": "MacBook Pro",
  "sku": "MBP-M2-16-512",
  "description": "MacBook Pro M2 16GB 512GB",
  "category": {
    "id": 3,
    "name": "电脑"
  },
  "cost_price": 8000.00,
  "selling_price": 9999.00,
  "min_stock_level": 5,
  "max_stock_level": 50,
  "current_stock": 0,
  "attributes": {
    "processor": "M2",
    "ram": "16GB",
    "storage": "512GB"
  },
  "created_at": "2025-04-14T03:45:00Z",
  "updated_at": "2025-04-14T03:45:00Z"
}
```

## 仓库管理

### 获取仓库列表

```
GET /warehouse/warehouses/
```

获取仓库列表。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为 1 |
| page_size | integer | 否 | 每页记录数，默认为 10 |
| search | string | 否 | 搜索关键词 |

**响应**:

```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "北京仓库",
      "code": "BJ001",
      "address": "北京市朝阳区xxx路123号",
      "contact_person": "张三",
      "contact_phone": "13800138000",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    // 更多仓库...
  ]
}
```

### 创建仓库

```
POST /warehouse/warehouses/
```

创建新仓库。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**请求体**:

```json
{
  "name": "上海仓库",
  "code": "SH001",
  "address": "上海市浦东新区xxx路456号",
  "contact_person": "李四",
  "contact_phone": "13900139000",
  "is_active": true
}
```

**响应**:

```json
{
  "id": 2,
  "name": "上海仓库",
  "code": "SH001",
  "address": "上海市浦东新区xxx路456号",
  "contact_person": "李四",
  "contact_phone": "13900139000",
  "is_active": true,
  "created_at": "2025-04-14T03:50:00Z",
  "updated_at": "2025-04-14T03:50:00Z"
}
```

### 获取区域列表

```
GET /warehouse/areas/
```

获取仓库区域列表。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为 1 |
| page_size | integer | 否 | 每页记录数，默认为 10 |
| warehouse | integer | 否 | 仓库 ID |

**响应**:

```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "A区",
      "code": "BJ-A",
      "warehouse": {
        "id": 1,
        "name": "北京仓库",
        "code": "BJ001"
      },
      "description": "普通货架区",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    // 更多区域...
  ]
}
```

### 获取位置列表

```
GET /warehouse/locations/
```

获取仓库位置列表。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为 1 |
| page_size | integer | 否 | 每页记录数，默认为 10 |
| warehouse | integer | 否 | 仓库 ID |
| area | integer | 否 | 区域 ID |

**响应**:

```json
{
  "count": 100,
  "next": "https://your-domain.com/api/warehouse/locations/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "A01-01",
      "code": "BJ-A-01-01",
      "warehouse": {
        "id": 1,
        "name": "北京仓库",
        "code": "BJ001"
      },
      "area": {
        "id": 1,
        "name": "A区",
        "code": "BJ-A"
      },
      "capacity": 100,
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    // 更多位置...
  ]
}
```

## 库存管理

### 获取库存列表

```
GET /inventory/inventory/
```

获取库存列表。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为 1 |
| page_size | integer | 否 | 每页记录数，默认为 10 |
| product | integer | 否 | 产品 ID |
| warehouse | integer | 否 | 仓库 ID |
| location | integer | 否 | 位置 ID |
| min_quantity | integer | 否 | 最小数量 |
| max_quantity | integer | 否 | 最大数量 |

**响应**:

```json
{
  "count": 200,
  "next": "https://your-domain.com/api/inventory/inventory/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "name": "iPhone 13",
        "sku": "IP13-128-BLK"
      },
      "warehouse": {
        "id": 1,
        "name": "北京仓库",
        "code": "BJ001"
      },
      "location": {
        "id": 1,
        "name": "A01-01",
        "code": "BJ-A-01-01"
      },
      "quantity": 45,
      "reserved_quantity": 5,
      "available_quantity": 40,
      "last_counted_at": "2025-03-01T00:00:00Z",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-04-01T00:00:00Z"
    },
    // 更多库存...
  ]
}
```

### 库存调整

```
POST /inventory/transactions/
```

创建库存调整交易。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**请求体**:

```json
{
  "inventory": 1,
  "quantity": 10,
  "transaction_type": "increase",
  "reference_type": "purchase_order",
  "reference_id": "PO-2025-001",
  "notes": "采购入库"
}
```

**响应**:

```json
{
  "id": 1,
  "inventory": {
    "id": 1,
    "product": {
      "id": 1,
      "name": "iPhone 13",
      "sku": "IP13-128-BLK"
    },
    "location": {
      "id": 1,
      "name": "A01-01",
      "code": "BJ-A-01-01"
    }
  },
  "quantity": 10,
  "transaction_type": "increase",
  "reference_type": "purchase_order",
  "reference_id": "PO-2025-001",
  "notes": "采购入库",
  "created_by": {
    "id": 1,
    "username": "admin"
  },
  "created_at": "2025-04-14T04:00:00Z"
}
```

### 库存移动

```
POST /inventory/movements/
```

在不同位置之间移动库存。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**请求体**:

```json
{
  "product": 1,
  "source_location": 1,
  "destination_location": 2,
  "quantity": 5,
  "notes": "库存重新分配"
}
```

**响应**:

```json
{
  "id": 1,
  "product": {
    "id": 1,
    "name": "iPhone 13",
    "sku": "IP13-128-BLK"
  },
  "source_location": {
    "id": 1,
    "name": "A01-01",
    "code": "BJ-A-01-01"
  },
  "destination_location": {
    "id": 2,
    "name": "A01-02",
    "code": "BJ-A-01-02"
  },
  "quantity": 5,
  "notes": "库存重新分配",
  "created_by": {
    "id": 1,
    "username": "admin"
  },
  "created_at": "2025-04-14T04:05:00Z"
}
```

### 批次管理

```
GET /inventory/batches/
```

获取批次列表。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为 1 |
| page_size | integer | 否 | 每页记录数，默认为 10 |
| product | integer | 否 | 产品 ID |
| batch_number | string | 否 | 批次号 |
| expiry_from | date | 否 | 最早过期日期 |
| expiry_to | date | 否 | 最晚过期日期 |

**响应**:

```json
{
  "count": 50,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "name": "iPhone 13",
        "sku": "IP13-128-BLK"
      },
      "batch_number": "IP13-2025-001",
      "production_date": "2025-01-15",
      "expiry_date": "2027-01-15",
      "quantity": 50,
      "notes": "第一批次",
      "created_at": "2025-01-20T00:00:00Z",
      "updated_at": "2025-01-20T00:00:00Z"
    },
    // 更多批次...
  ]
}
```

## 入库管理

### 获取采购订单列表

```
GET /inventory/purchase-orders/
```

获取采购订单列表。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为 1 |
| page_size | integer | 否 | 每页记录数，默认为 10 |
| status | string | 否 | 订单状态 |
| date_from | date | 否 | 最早日期 |
| date_to | date | 否 | 最晚日期 |

**响应**:

```json
{
  "count": 20,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "order_number": "PO-2025-001",
      "supplier": {
        "id": 1,
        "name": "苹果官方供应商"
      },
      "status": "received",
      "order_date": "2025-01-10",
      "expected_date": "2025-01-20",
      "received_date": "2025-01-18",
      "total_amount": 250000.00,
      "notes": "第一季度采购",
      "items": [
        {
          "id": 1,
          "product": {
            "id": 1,
            "name": "iPhone 13",
            "sku": "IP13-128-BLK"
          },
          "ordered_quantity": 50,
          "received_quantity": 50,
          "unit_price": 5000.00,
          "total_price": 250000.00
        }
      ],
      "created_by": {
        "id": 1,
        "username": "admin"
      },
      "created_at": "2025-01-10T00:00:00Z",
      "updated_at": "2025-01-18T00:00:00Z"
    },
    // 更多采购订单...
  ]
}
```

### 创建采购订单

```
POST /inventory/purchase-orders/
```

创建新的采购订单。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**请求体**:

```json
{
  "supplier": 1,
  "expected_date": "2025-05-01",
  "notes": "第二季度采购",
  "items": [
    {
      "product": 1,
      "ordered_quantity": 30,
      "unit_price": 5000.00
    },
    {
      "product": 2,
      "ordered_quantity": 10,
      "unit_price": 8000.00
    }
  ]
}
```

**响应**:

```json
{
  "id": 2,
  "order_number": "PO-2025-002",
  "supplier": {
    "id": 1,
    "name": "苹果官方供应商"
  },
  "status": "pending",
  "order_date": "2025-04-14",
  "expected_date": "2025-05-01",
  "received_date": null,
  "total_amount": 230000.00,
  "notes": "第二季度采购",
  "items": [
    {
      "id": 2,
      "product": {
        "id": 1,
        "name": "iPhone 13",
        "sku": "IP13-128-BLK"
      },
      "ordered_quantity": 30,
      "received_quantity": 0,
      "unit_price": 5000.00,
      "total_price": 150000.00
    },
    {
      "id": 3,
      "product": {
        "id": 2,
        "name": "MacBook Pro",
        "sku": "MBP-M2-16-512"
      },
      "ordered_quantity": 10,
      "received_quantity": 0,
      "unit_price": 8000.00,
      "total_price": 80000.00
    }
  ],
  "created_by": {
    "id": 1,
    "username": "admin"
  },
  "created_at": "2025-04-14T04:10:00Z",
  "updated_at": "2025-04-14T04:10:00Z"
}
```

## 出库管理

### 获取销售订单列表

```
GET /inventory/sales-orders/
```

获取销售订单列表。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为 1 |
| page_size | integer | 否 | 每页记录数，默认为 10 |
| status | string | 否 | 订单状态 |
| date_from | date | 否 | 最早日期 |
| date_to | date | 否 | 最晚日期 |

**响应**:

```json
{
  "count": 15,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "order_number": "SO-2025-001",
      "customer": {
        "id": 1,
        "name": "北京科技有限公司"
      },
      "status": "shipped",
      "order_date": "2025-02-10",
      "shipping_date": "2025-02-15",
      "total_amount": 20997.00,
      "notes": "优先客户订单",
      "items": [
        {
          "id": 1,
          "product": {
            "id": 1,
            "name": "iPhone 13",
            "sku": "IP13-128-BLK"
          },
          "ordered_quantity": 3,
          "shipped_quantity": 3,
          "unit_price": 6999.00,
          "total_price": 20997.00
        }
      ],
      "created_by": {
        "id": 1,
        "username": "admin"
      },
      "created_at": "2025-02-10T00:00:00Z",
      "updated_at": "2025-02-15T00:00:00Z"
    },
    // 更多销售订单...
  ]
}
```

### 创建销售订单

```
POST /inventory/sales-orders/
```

创建新的销售订单。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**请求体**:

```json
{
  "customer": 1,
  "notes": "季度末促销订单",
  "items": [
    {
      "product": 1,
      "ordered_quantity": 5,
      "unit_price": 6999.00
    },
    {
      "product": 2,
      "ordered_quantity": 2,
      "unit_price": 9999.00
    }
  ]
}
```

**响应**:

```json
{
  "id": 2,
  "order_number": "SO-2025-002",
  "customer": {
    "id": 1,
    "name": "北京科技有限公司"
  },
  "status": "pending",
  "order_date": "2025-04-14",
  "shipping_date": null,
  "total_amount": 54993.00,
  "notes": "季度末促销订单",
  "items": [
    {
      "id": 2,
      "product": {
        "id": 1,
        "name": "iPhone 13",
        "sku": "IP13-128-BLK"
      },
      "ordered_quantity": 5,
      "shipped_quantity": 0,
      "unit_price": 6999.00,
      "total_price": 34995.00
    },
    {
      "id": 3,
      "product": {
        "id": 2,
        "name": "MacBook Pro",
        "sku": "MBP-M2-16-512"
      },
      "ordered_quantity": 2,
      "shipped_quantity": 0,
      "unit_price": 9999.00,
      "total_price": 19998.00
    }
  ],
  "created_by": {
    "id": 1,
    "username": "admin"
  },
  "created_at": "2025-04-14T04:15:00Z",
  "updated_at": "2025-04-14T04:15:00Z"
}
```

## 任务管理

### 获取任务列表

```
GET /warehouse/tasks/
```

获取仓库任务列表。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为 1 |
| page_size | integer | 否 | 每页记录数，默认为 10 |
| task_type | string | 否 | 任务类型 |
| status | string | 否 | 任务状态 |
| assigned_to | integer | 否 | 分配给的用户 ID |
| warehouse | integer | 否 | 仓库 ID |

**响应**:

```json
{
  "count": 30,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "task_number": "TASK-2025-001",
      "task_type": "receiving",
      "status": "completed",
      "priority": "high",
      "reference_type": "purchase_order",
      "reference_id": "PO-2025-001",
      "warehouse": {
        "id": 1,
        "name": "北京仓库",
        "code": "BJ001"
      },
      "assigned_to": {
        "id": 2,
        "username": "warehousestaff"
      },
      "description": "接收采购订单 PO-2025-001",
      "start_time": "2025-01-18T09:00:00Z",
      "end_time": "2025-01-18T10:30:00Z",
      "created_by": {
        "id": 1,
        "username": "admin"
      },
      "created_at": "2025-01-17T00:00:00Z",
      "updated_at": "2025-01-18T10:30:00Z"
    },
    // 更多任务...
  ]
}
```

### 创建任务

```
POST /warehouse/tasks/
```

创建新的仓库任务。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**请求体**:

```json
{
  "task_type": "picking",
  "priority": "medium",
  "reference_type": "sales_order",
  "reference_id": "SO-2025-002",
  "warehouse": 1,
  "assigned_to": 2,
  "description": "为销售订单 SO-2025-002 拣货"
}
```

**响应**:

```json
{
  "id": 2,
  "task_number": "TASK-2025-002",
  "task_type": "picking",
  "status": "pending",
  "priority": "medium",
  "reference_type": "sales_order",
  "reference_id": "SO-2025-002",
  "warehouse": {
    "id": 1,
    "name": "北京仓库",
    "code": "BJ001"
  },
  "assigned_to": {
    "id": 2,
    "username": "warehousestaff"
  },
  "description": "为销售订单 SO-2025-002 拣货",
  "start_time": null,
  "end_time": null,
  "created_by": {
    "id": 1,
    "username": "admin"
  },
  "created_at": "2025-04-14T04:20:00Z",
  "updated_at": "2025-04-14T04:20:00Z"
}
```

### 更新任务状态

```
PATCH /warehouse/tasks/{id}/
```

更新任务状态。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**请求体**:

```json
{
  "status": "in_progress",
  "start_time": "2025-04-14T04:30:00Z"
}
```

**响应**:

```json
{
  "id": 2,
  "task_number": "TASK-2025-002",
  "task_type": "picking",
  "status": "in_progress",
  "priority": "medium",
  "reference_type": "sales_order",
  "reference_id": "SO-2025-002",
  "warehouse": {
    "id": 1,
    "name": "北京仓库",
    "code": "BJ001"
  },
  "assigned_to": {
    "id": 2,
    "username": "warehousestaff"
  },
  "description": "为销售订单 SO-2025-002 拣货",
  "start_time": "2025-04-14T04:30:00Z",
  "end_time": null,
  "created_by": {
    "id": 1,
    "username": "admin"
  },
  "created_at": "2025-04-14T04:20:00Z",
  "updated_at": "2025-04-14T04:30:00Z"
}
```

## 报表和分析

### 获取报表列表

```
GET /reports/reports/
```

获取报表列表。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为 1 |
| page_size | integer | 否 | 每页记录数，默认为 10 |
| report_type | string | 否 | 报表类型 |

**响应**:

```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "库存状态报表",
      "report_type": "inventory_status",
      "description": "显示当前库存水平和价值",
      "parameters": {
        "warehouse": null,
        "category": null
      },
      "created_by": {
        "id": 1,
        "username": "admin"
      },
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    // 更多报表...
  ]
}
```

### 执行报表

```
POST /reports/reports/{id}/execute/
```

执行指定报表。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**请求体**:

```json
{
  "parameters": {
    "warehouse": 1,
    "date_from": "2025-01-01",
    "date_to": "2025-04-14"
  },
  "format": "json"
}
```

**响应**:

```json
{
  "id": "report-2025-04-14-001",
  "report": {
    "id": 1,
    "name": "库存状态报表"
  },
  "status": "completed",
  "parameters": {
    "warehouse": 1,
    "date_from": "2025-01-01",
    "date_to": "2025-04-14"
  },
  "result": {
    "summary": {
      "total_products": 2,
      "total_quantity": 45,
      "total_value": 225000.00,
      "low_stock_items": 0
    },
    "details": [
      {
        "product": {
          "id": 1,
          "name": "iPhone 13",
          "sku": "IP13-128-BLK"
        },
        "quantity": 45,
        "value": 225000.00,
        "status": "normal"
      },
      // 更多产品...
    ]
  },
  "created_by": {
    "id": 1,
    "username": "admin"
  },
  "created_at": "2025-04-14T04:35:00Z"
}
```

### 获取仪表板列表

```
GET /reports/dashboards/
```

获取仪表板列表。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为 1 |
| page_size | integer | 否 | 每页记录数，默认为 10 |

**响应**:

```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "库存概览仪表板",
      "description": "显示库存关键指标",
      "is_default": true,
      "widgets": [
        {
          "id": 1,
          "title": "库存价值趋势",
          "widget_type": "chart",
          "data_source": "inventory_value_trend",
          "position_x": 0,
          "position_y": 0,
          "width": 6,
          "height": 4
        },
        // 更多小部件...
      ],
      "created_by": {
        "id": 1,
        "username": "admin"
      },
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    // 更多仪表板...
  ]
}
```

### 获取KPI列表

```
GET /reports/kpis/
```

获取KPI列表。

**请求头**:

| 头部名称 | 描述 |
|----------|------|
| Authorization | Bearer {access_token} |
| X-Tenant-ID | 租户 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| page | integer | 否 | 页码，默认为 1 |
| page_size | integer | 否 | 每页记录数，默认为 10 |
| category | string | 否 | KPI类别 |

**响应**:

```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "库存周转率",
      "category": "inventory",
      "description": "衡量库存周转效率",
      "calculation_method": "销售成本 / 平均库存",
      "unit": "次/年",
      "target_value": 5.0,
      "current_value": 4.5,
      "status": "warning",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-04-01T00:00:00Z"
    },
    // 更多KPI...
  ]
}
```

## 错误处理

API 使用标准 HTTP 状态码表示请求结果：

- 200 OK: 请求成功
- 201 Created: 资源创建成功
- 204 No Content: 请求成功但无返回内容
- 400 Bad Request: 请求参数错误
- 401 Unauthorized: 认证失败
- 403 Forbidden: 权限不足
- 404 Not Found: 资源不存在
- 500 Internal Server Error: 服务器内部错误

错误响应格式：

```json
{
  "error": {
    "code": "invalid_request",
    "message": "请求参数无效",
    "details": {
      "field_name": [
        "错误描述"
      ]
    }
  }
}
```

## 分页

所有列表 API 都支持分页，默认每页返回 10 条记录。分页参数：

- `page`: 页码，从 1 开始
- `page_size`: 每页记录数，最大 100

分页响应格式：

```json
{
  "count": 100,
  "next": "https://your-domain.com/api/resource/?page=2",
  "previous": null,
  "results": [
    // 资源列表
  ]
}
```

## 筛选和排序

大多数列表 API 支持筛选和排序：

- 筛选：使用字段名作为查询参数，如 `?status=active`
- 排序：使用 `ordering` 参数，如 `?ordering=name` 或 `?ordering=-created_at`（降序）

## 版本控制

API 版本通过 URL 路径指定，当前版本为 v1：

```
https://your-domain.com/api/v1/resource/
```

## 速率限制

API 实施速率限制以防止滥用：

- 认证用户：每分钟 60 个请求
- 匿名用户：每分钟 20 个请求

超出限制时返回 HTTP 429 状态码。
