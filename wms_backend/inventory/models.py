from django.db import models
from django.utils import timezone
from core.models import TenantAwareModel
from warehouse.models import Location
from accounts.models import User

class Product(TenantAwareModel):
    """产品模型"""
    name = models.CharField(max_length=255, verbose_name="产品名称")
    sku = models.CharField(max_length=50, verbose_name="SKU", unique=True)
    barcode = models.CharField(max_length=50, verbose_name="条形码", blank=True, null=True)
    description = models.TextField(verbose_name="描述", blank=True, null=True)
    category = models.ForeignKey('ProductCategory', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="类别")
    
    # 价格信息
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="成本价", blank=True, null=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="销售价", blank=True, null=True)
    
    # 库存控制
    min_stock_level = models.IntegerField(default=0, verbose_name="最低库存水平")
    reorder_point = models.IntegerField(default=0, verbose_name="再订购点")
    
    # 物理属性
    weight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="重量(kg)", blank=True, null=True)
    length = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="长度(cm)", blank=True, null=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="宽度(cm)", blank=True, null=True)
    height = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="高度(cm)", blank=True, null=True)
    
    # 处理信息
    handling_instructions = models.TextField(verbose_name="处理说明", blank=True, null=True)
    storage_requirements = models.TextField(verbose_name="存储要求", blank=True, null=True)
    
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    class Meta:
        verbose_name = "产品"
        verbose_name_plural = "产品"
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['barcode']),
            models.Index(fields=['category']),
        ]

class ProductCategory(TenantAwareModel):
    """产品类别模型"""
    name = models.CharField(max_length=100, verbose_name="类别名称")
    description = models.TextField(verbose_name="描述", blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, verbose_name="父类别")
    
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "产品类别"
        verbose_name_plural = "产品类别"
        ordering = ['name']

class ProductAttribute(TenantAwareModel):
    """产品属性模型"""
    name = models.CharField(max_length=100, verbose_name="属性名称")
    description = models.TextField(verbose_name="描述", blank=True, null=True)
    
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "产品属性"
        verbose_name_plural = "产品属性"
        ordering = ['name']

class ProductAttributeValue(TenantAwareModel):
    """产品属性值模型"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attribute_values', verbose_name="产品")
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, verbose_name="属性")
    value = models.CharField(max_length=255, verbose_name="属性值")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}: {self.value}"
    
    class Meta:
        verbose_name = "产品属性值"
        verbose_name_plural = "产品属性值"
        unique_together = ('product', 'attribute')

class ProductImage(TenantAwareModel):
    """产品图片模型"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="产品")
    image = models.ImageField(upload_to='products/', verbose_name="图片")
    is_primary = models.BooleanField(default=False, verbose_name="是否主图")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    def __str__(self):
        return f"{self.product.name} - {'主图' if self.is_primary else '图片'}"
    
    class Meta:
        verbose_name = "产品图片"
        verbose_name_plural = "产品图片"

class Batch(TenantAwareModel):
    """批次模型"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches', verbose_name="产品")
    batch_number = models.CharField(max_length=50, verbose_name="批次号")
    manufacturing_date = models.DateField(blank=True, null=True, verbose_name="生产日期")
    expiry_date = models.DateField(blank=True, null=True, verbose_name="到期日期")
    received_date = models.DateField(default=timezone.now, verbose_name="接收日期")
    supplier = models.CharField(max_length=255, blank=True, null=True, verbose_name="供应商")
    notes = models.TextField(blank=True, null=True, verbose_name="备注")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    def __str__(self):
        return f"{self.product.name} - {self.batch_number}"
    
    class Meta:
        verbose_name = "批次"
        verbose_name_plural = "批次"
        unique_together = ('product', 'batch_number')
        indexes = [
            models.Index(fields=['batch_number']),
            models.Index(fields=['expiry_date']),
        ]

class SerialNumber(TenantAwareModel):
    """序列号模型"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='serial_numbers', verbose_name="产品")
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, blank=True, null=True, related_name='serial_numbers', verbose_name="批次")
    serial_number = models.CharField(max_length=50, verbose_name="序列号")
    status = models.CharField(max_length=20, choices=[
        ('available', '可用'),
        ('reserved', '已预留'),
        ('sold', '已售出'),
        ('damaged', '已损坏'),
        ('returned', '已退回'),
    ], default='available', verbose_name="状态")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="位置")
    notes = models.TextField(blank=True, null=True, verbose_name="备注")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    def __str__(self):
        return f"{self.product.name} - {self.serial_number}"
    
    class Meta:
        verbose_name = "序列号"
        verbose_name_plural = "序列号"
        unique_together = ('product', 'serial_number')
        indexes = [
            models.Index(fields=['serial_number']),
            models.Index(fields=['status']),
        ]

class Inventory(TenantAwareModel):
    """库存模型"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory', verbose_name="产品")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='inventory', verbose_name="位置")
    quantity = models.IntegerField(default=0, verbose_name="数量")
    reserved_quantity = models.IntegerField(default=0, verbose_name="预留数量")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    @property
    def available_quantity(self):
        """可用数量"""
        return max(0, self.quantity - self.reserved_quantity)
    
    def __str__(self):
        return f"{self.product.name} @ {self.location.name}: {self.quantity}"
    
    class Meta:
        verbose_name = "库存"
        verbose_name_plural = "库存"
        unique_together = ('product', 'location')
        indexes = [
            models.Index(fields=['product', 'location']),
        ]

class BatchInventory(TenantAwareModel):
    """批次库存模型"""
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='batch_inventory', verbose_name="库存")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='batch_inventory', verbose_name="批次")
    quantity = models.IntegerField(default=0, verbose_name="数量")
    reserved_quantity = models.IntegerField(default=0, verbose_name="预留数量")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    @property
    def available_quantity(self):
        """可用数量"""
        return max(0, self.quantity - self.reserved_quantity)
    
    def __str__(self):
        return f"{self.inventory.product.name} @ {self.inventory.location.name} - {self.batch.batch_number}: {self.quantity}"
    
    class Meta:
        verbose_name = "批次库存"
        verbose_name_plural = "批次库存"
        unique_together = ('inventory', 'batch')

class InventoryTransaction(TenantAwareModel):
    """库存交易记录模型"""
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='transactions', verbose_name="库存")
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, blank=True, null=True, related_name='transactions', verbose_name="批次")
    transaction_type = models.CharField(max_length=20, choices=[
        ('increase', '增加'),
        ('decrease', '减少'),
    ], verbose_name="交易类型")
    quantity = models.IntegerField(verbose_name="数量")
    previous_quantity = models.IntegerField(verbose_name="之前数量")
    new_quantity = models.IntegerField(verbose_name="新数量")
    reference_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="引用类型")
    reference_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="引用ID")
    notes = models.TextField(blank=True, null=True, verbose_name="备注")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="操作人")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    def __str__(self):
        return f"{self.inventory.product.name} @ {self.inventory.location.name} - {self.transaction_type}: {self.quantity}"
    
    class Meta:
        verbose_name = "库存交易记录"
        verbose_name_plural = "库存交易记录"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]

class InventoryCount(TenantAwareModel):
    """库存盘点模型"""
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='inventory_counts', verbose_name="位置")
    count_type = models.CharField(max_length=20, choices=[
        ('cycle', '周期盘点'),
        ('full', '全面盘点'),
        ('sample', '抽样盘点'),
    ], default='cycle', verbose_name="盘点类型")
    status = models.CharField(max_length=20, choices=[
        ('pending', '待处理'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ], default='pending', verbose_name="状态")
    started_at = models.DateTimeField(blank=True, null=True, verbose_name="开始时间")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="完成时间")
    notes = models.TextField(blank=True, null=True, verbose_name="备注")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='created_counts', verbose_name="创建人")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='assigned_counts', verbose_name="分配给")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    def __str__(self):
        return f"{self.location.name} - {self.get_count_type_display()} ({self.get_status_display()})"
    
    class Meta:
        verbose_name = "库存盘点"
        verbose_name_plural = "库存盘点"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['count_type']),
        ]

class InventoryCountItem(TenantAwareModel):
    """库存盘点项目模型"""
    inventory_count = models.ForeignKey(InventoryCount, on_delete=models.CASCADE, related_name='items', verbose_name="库存盘点")
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='count_items', verbose_name="库存")
    expected_quantity = models.IntegerField(verbose_name="预期数量")
    counted_quantity = models.IntegerField(blank=True, null=True, verbose_name="盘点数量")
    is_discrepancy = models.BooleanField(default=False, verbose_name="是否有差异")
    notes = models.TextField(blank=True, null=True, verbose_name="备注")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    def __str__(self):
        return f"{self.inventory.product.name} - 预期: {self.expected_quantity}, 实际: {self.counted_quantity or '未盘点'}"
    
    class Meta:
        verbose_name = "库存盘点项目"
        verbose_name_plural = "库存盘点项目"
        unique_together = ('inventory_count', 'inventory')

class InventoryAlert(TenantAwareModel):
    """库存警报模型"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='alerts', verbose_name="产品")
    alert_type = models.CharField(max_length=20, choices=[
        ('low_stock', '低库存'),
        ('out_of_stock', '缺货'),
        ('expiring', '即将过期'),
        ('expired', '已过期'),
    ], verbose_name="警报类型")
    status = models.CharField(max_length=20, choices=[
        ('active', '激活'),
        ('acknowledged', '已确认'),
        ('resolved', '已解决'),
    ], default='active', verbose_name="状态")
    message = models.TextField(verbose_name="消息")
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='acknowledged_alerts', verbose_name="确认人")
    acknowledged_at = models.DateTimeField(blank=True, null=True, verbose_name="确认时间")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    def __str__(self):
        return f"{self.product.name} - {self.get_alert_type_display()}"
    
    class Meta:
        verbose_name = "库存警报"
        verbose_name_plural = "库存警报"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type']),
            models.Index(fields=['status']),
        ]
