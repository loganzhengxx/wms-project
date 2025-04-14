# 智能库存系统数据库设计

## 1. 多租户架构

### Tenant（租户）
- `id`: 主键
- `name`: 租户名称
- `subdomain`: 子域名
- `created_at`: 创建时间
- `updated_at`: 更新时间
- `is_active`: 是否激活
- `settings`: JSON字段，存储租户特定设置

## 2. 用户和权限管理

### User（用户）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `username`: 用户名
- `email`: 电子邮件
- `password`: 密码（加密存储）
- `first_name`: 名
- `last_name`: 姓
- `is_active`: 是否激活
- `is_staff`: 是否员工
- `is_admin`: 是否管理员
- `is_superuser`: 是否超级用户
- `last_login`: 最后登录时间
- `created_at`: 创建时间
- `updated_at`: 更新时间

### Role（角色）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `name`: 角色名称
- `description`: 角色描述
- `created_at`: 创建时间
- `updated_at`: 更新时间

### Permission（权限）
- `id`: 主键
- `name`: 权限名称
- `codename`: 权限代码
- `description`: 权限描述

### RolePermission（角色权限）
- `id`: 主键
- `role_id`: 外键，关联Role
- `permission_id`: 外键，关联Permission

### UserRole（用户角色）
- `id`: 主键
- `user_id`: 外键，关联User
- `role_id`: 外键，关联Role

## 3. 产品管理

### Category（产品类别）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `name`: 类别名称
- `description`: 类别描述
- `parent_id`: 外键，关联Category（自引用，用于层级分类）
- `created_at`: 创建时间
- `updated_at`: 更新时间

### Product（产品）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `name`: 产品名称
- `description`: 产品描述
- `sku`: 库存单位
- `barcode`: 条形码
- `category_id`: 外键，关联Category
- `weight`: 重量
- `width`: 宽度
- `height`: 高度
- `length`: 长度
- `cost_price`: 成本价
- `selling_price`: 销售价
- `min_stock_level`: 最低库存水平
- `reorder_point`: 再订购点
- `handling_instructions`: 处理说明
- `storage_requirements`: 存储要求
- `is_active`: 是否激活
- `created_at`: 创建时间
- `updated_at`: 更新时间

### ProductAttribute（产品属性）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `name`: 属性名称
- `description`: 属性描述

### ProductAttributeValue（产品属性值）
- `id`: 主键
- `product_id`: 外键，关联Product
- `attribute_id`: 外键，关联ProductAttribute
- `value`: 属性值

### ProductImage（产品图片）
- `id`: 主键
- `product_id`: 外键，关联Product
- `image_url`: 图片URL
- `is_primary`: 是否主图
- `created_at`: 创建时间

### Supplier（供应商）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `name`: 供应商名称
- `contact_person`: 联系人
- `email`: 电子邮件
- `phone`: 电话
- `address`: 地址
- `is_active`: 是否激活
- `created_at`: 创建时间
- `updated_at`: 更新时间

### ProductSupplier（产品供应商）
- `id`: 主键
- `product_id`: 外键，关联Product
- `supplier_id`: 外键，关联Supplier
- `supplier_sku`: 供应商SKU
- `lead_time`: 交货时间（天）
- `min_order_quantity`: 最小订购量
- `price`: 价格
- `is_primary`: 是否主要供应商
- `created_at`: 创建时间
- `updated_at`: 更新时间

## 4. 仓库和位置管理

### Warehouse（仓库）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `name`: 仓库名称
- `code`: 仓库代码
- `address`: 地址
- `contact_person`: 联系人
- `phone`: 电话
- `email`: 电子邮件
- `is_active`: 是否激活
- `created_at`: 创建时间
- `updated_at`: 更新时间

### Zone（区域）
- `id`: 主键
- `warehouse_id`: 外键，关联Warehouse
- `name`: 区域名称
- `code`: 区域代码
- `description`: 区域描述
- `zone_type`: 区域类型（存储、拣货、收货、发货等）
- `created_at`: 创建时间
- `updated_at`: 更新时间

### Location（位置）
- `id`: 主键
- `warehouse_id`: 外键，关联Warehouse
- `zone_id`: 外键，关联Zone
- `name`: 位置名称
- `code`: 位置代码
- `barcode`: 条形码
- `location_type`: 位置类型（货架、货位、地面等）
- `aisle`: 通道
- `rack`: 货架
- `shelf`: 层
- `bin`: 格
- `max_weight`: 最大承重
- `max_volume`: 最大体积
- `is_pickable`: 是否可拣货
- `is_receivable`: 是否可收货
- `is_active`: 是否激活
- `created_at`: 创建时间
- `updated_at`: 更新时间

## 5. 库存管理

### Inventory（库存）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `product_id`: 外键，关联Product
- `warehouse_id`: 外键，关联Warehouse
- `location_id`: 外键，关联Location
- `quantity`: 数量
- `reserved_quantity`: 预留数量
- `available_quantity`: 可用数量（计算字段：quantity - reserved_quantity）
- `created_at`: 创建时间
- `updated_at`: 更新时间

### Batch（批次）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `product_id`: 外键，关联Product
- `batch_number`: 批次号
- `expiry_date`: 过期日期
- `manufacturing_date`: 生产日期
- `received_date`: 接收日期
- `cost_price`: 成本价
- `notes`: 备注
- `created_at`: 创建时间
- `updated_at`: 更新时间

### BatchInventory（批次库存）
- `id`: 主键
- `batch_id`: 外键，关联Batch
- `inventory_id`: 外键，关联Inventory
- `quantity`: 数量
- `reserved_quantity`: 预留数量
- `created_at`: 创建时间
- `updated_at`: 更新时间

### InventoryTransaction（库存交易）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `product_id`: 外键，关联Product
- `batch_id`: 外键，关联Batch（可为空）
- `warehouse_id`: 外键，关联Warehouse
- `location_id`: 外键，关联Location
- `reference_type`: 引用类型（收货、发货、调整等）
- `reference_id`: 引用ID
- `transaction_type`: 交易类型（增加、减少）
- `quantity`: 数量
- `previous_quantity`: 之前数量
- `new_quantity`: 新数量
- `user_id`: 外键，关联User
- `notes`: 备注
- `created_at`: 创建时间

### StockAdjustment（库存调整）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `warehouse_id`: 外键，关联Warehouse
- `adjustment_number`: 调整编号
- `adjustment_date`: 调整日期
- `reason`: 调整原因
- `notes`: 备注
- `status`: 状态（草稿、已确认、已取消）
- `user_id`: 外键，关联User
- `created_at`: 创建时间
- `updated_at`: 更新时间

### StockAdjustmentItem（库存调整项）
- `id`: 主键
- `adjustment_id`: 外键，关联StockAdjustment
- `product_id`: 外键，关联Product
- `batch_id`: 外键，关联Batch（可为空）
- `location_id`: 外键，关联Location
- `quantity_before`: 调整前数量
- `quantity_after`: 调整后数量
- `adjustment_quantity`: 调整数量（计算字段：quantity_after - quantity_before）
- `reason`: 调整原因
- `created_at`: 创建时间
- `updated_at`: 更新时间

### StockCount（盘点）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `warehouse_id`: 外键，关联Warehouse
- `count_number`: 盘点编号
- `count_date`: 盘点日期
- `count_type`: 盘点类型（全面盘点、周期盘点）
- `status`: 状态（草稿、进行中、已完成、已取消）
- `notes`: 备注
- `user_id`: 外键，关联User
- `created_at`: 创建时间
- `updated_at`: 更新时间

### StockCountItem（盘点项）
- `id`: 主键
- `count_id`: 外键，关联StockCount
- `product_id`: 外键，关联Product
- `batch_id`: 外键，关联Batch（可为空）
- `location_id`: 外键，关联Location
- `expected_quantity`: 预期数量
- `counted_quantity`: 盘点数量
- `variance`: 差异（计算字段：counted_quantity - expected_quantity）
- `status`: 状态（待盘点、已盘点、已调整）
- `created_at`: 创建时间
- `updated_at`: 更新时间

## 6. 入库管理

### PurchaseOrder（采购订单）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `order_number`: 订单编号
- `supplier_id`: 外键，关联Supplier
- `warehouse_id`: 外键，关联Warehouse
- `order_date`: 订单日期
- `expected_delivery_date`: 预计交货日期
- `status`: 状态（草稿、已确认、部分收货、已完成、已取消）
- `total_amount`: 总金额
- `notes`: 备注
- `user_id`: 外键，关联User
- `created_at`: 创建时间
- `updated_at`: 更新时间

### PurchaseOrderItem（采购订单项）
- `id`: 主键
- `purchase_order_id`: 外键，关联PurchaseOrder
- `product_id`: 外键，关联Product
- `ordered_quantity`: 订购数量
- `received_quantity`: 已收货数量
- `unit_price`: 单价
- `total_price`: 总价（计算字段：ordered_quantity * unit_price）
- `created_at`: 创建时间
- `updated_at`: 更新时间

### GoodsReceipt（收货单）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `receipt_number`: 收货单编号
- `purchase_order_id`: 外键，关联PurchaseOrder（可为空）
- `supplier_id`: 外键，关联Supplier
- `warehouse_id`: 外键，关联Warehouse
- `receipt_date`: 收货日期
- `status`: 状态（草稿、已确认、已取消）
- `notes`: 备注
- `user_id`: 外键，关联User
- `created_at`: 创建时间
- `updated_at`: 更新时间

### GoodsReceiptItem（收货单项）
- `id`: 主键
- `goods_receipt_id`: 外键，关联GoodsReceipt
- `purchase_order_item_id`: 外键，关联PurchaseOrderItem（可为空）
- `product_id`: 外键，关联Product
- `batch_id`: 外键，关联Batch（可为空）
- `location_id`: 外键，关联Location
- `expected_quantity`: 预期数量
- `received_quantity`: 收货数量
- `unit_price`: 单价
- `total_price`: 总价（计算字段：received_quantity * unit_price）
- `quality_check_status`: 质检状态（待检、合格、不合格）
- `created_at`: 创建时间
- `updated_at`: 更新时间

## 7. 出库管理

### SalesOrder（销售订单）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `order_number`: 订单编号
- `customer_name`: 客户名称
- `customer_email`: 客户电子邮件
- `customer_phone`: 客户电话
- `shipping_address`: 配送地址
- `warehouse_id`: 外键，关联Warehouse
- `order_date`: 订单日期
- `expected_shipping_date`: 预计发货日期
- `status`: 状态（草稿、已确认、部分发货、已完成、已取消）
- `total_amount`: 总金额
- `notes`: 备注
- `user_id`: 外键，关联User
- `created_at`: 创建时间
- `updated_at`: 更新时间

### SalesOrderItem（销售订单项）
- `id`: 主键
- `sales_order_id`: 外键，关联SalesOrder
- `product_id`: 外键，关联Product
- `ordered_quantity`: 订购数量
- `shipped_quantity`: 已发货数量
- `unit_price`: 单价
- `total_price`: 总价（计算字段：ordered_quantity * unit_price）
- `created_at`: 创建时间
- `updated_at`: 更新时间

### PickList（拣货单）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `pick_number`: 拣货单编号
- `sales_order_id`: 外键，关联SalesOrder
- `warehouse_id`: 外键，关联Warehouse
- `pick_date`: 拣货日期
- `status`: 状态（待拣货、部分拣货、已完成、已取消）
- `assigned_user_id`: 外键，关联User（分配给谁）
- `notes`: 备注
- `created_at`: 创建时间
- `updated_at`: 更新时间

### PickListItem（拣货单项）
- `id`: 主键
- `pick_list_id`: 外键，关联PickList
- `sales_order_item_id`: 外键，关联SalesOrderItem
- `product_id`: 外键，关联Product
- `batch_id`: 外键，关联Batch（可为空）
- `location_id`: 外键，关联Location
- `quantity_to_pick`: 待拣货数量
- `picked_quantity`: 已拣货数量
- `status`: 状态（待拣货、已拣货、部分拣货）
- `created_at`: 创建时间
- `updated_at`: 更新时间

### Shipment（发货单）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `shipment_number`: 发货单编号
- `sales_order_id`: 外键，关联SalesOrder
- `warehouse_id`: 外键，关联Warehouse
- `shipment_date`: 发货日期
- `carrier`: 承运商
- `tracking_number`: 跟踪号
- `status`: 状态（草稿、已确认、已发货、已取消）
- `notes`: 备注
- `user_id`: 外键，关联User
- `created_at`: 创建时间
- `updated_at`: 更新时间

### ShipmentItem（发货单项）
- `id`: 主键
- `shipment_id`: 外键，关联Shipment
- `sales_order_item_id`: 外键，关联SalesOrderItem
- `product_id`: 外键，关联Product
- `batch_id`: 外键，关联Batch（可为空）
- `quantity`: 发货数量
- `created_at`: 创建时间
- `updated_at`: 更新时间

## 8. 任务管理

### Task（任务）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `warehouse_id`: 外键，关联Warehouse
- `task_type`: 任务类型（收货、上架、拣货、盘点等）
- `reference_type`: 引用类型
- `reference_id`: 引用ID
- `priority`: 优先级（低、中、高）
- `status`: 状态（待分配、已分配、进行中、已完成、已取消）
- `assigned_user_id`: 外键，关联User（分配给谁）
- `start_time`: 开始时间
- `end_time`: 结束时间
- `notes`: 备注
- `created_at`: 创建时间
- `updated_at`: 更新时间

### TaskHistory（任务历史）
- `id`: 主键
- `task_id`: 外键，关联Task
- `status`: 状态
- `user_id`: 外键，关联User
- `notes`: 备注
- `created_at`: 创建时间

## 9. 报表和分析

### Report（报表）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `name`: 报表名称
- `description`: 报表描述
- `report_type`: 报表类型
- `query`: 查询语句
- `parameters`: JSON字段，存储报表参数
- `created_at`: 创建时间
- `updated_at`: 更新时间

### ReportSchedule（报表计划）
- `id`: 主键
- `report_id`: 外键，关联Report
- `name`: 计划名称
- `frequency`: 频率（每日、每周、每月）
- `recipients`: JSON字段，存储接收者列表
- `is_active`: 是否激活
- `last_run`: 最后运行时间
- `created_at`: 创建时间
- `updated_at`: 更新时间

## 10. 系统配置

### Setting（设置）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant（可为空，为空表示系统级设置）
- `group`: 分组
- `key`: 键
- `value`: 值
- `description`: 描述
- `created_at`: 创建时间
- `updated_at`: 更新时间

### Notification（通知）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `user_id`: 外键，关联User
- `title`: 标题
- `message`: 消息内容
- `notification_type`: 通知类型
- `is_read`: 是否已读
- `reference_type`: 引用类型
- `reference_id`: 引用ID
- `created_at`: 创建时间
- `updated_at`: 更新时间

### AuditLog（审计日志）
- `id`: 主键
- `tenant_id`: 外键，关联Tenant
- `user_id`: 外键，关联User
- `action`: 操作
- `entity_type`: 实体类型
- `entity_id`: 实体ID
- `old_values`: JSON字段，存储旧值
- `new_values`: JSON字段，存储新值
- `ip_address`: IP地址
- `user_agent`: 用户代理
- `created_at`: 创建时间
