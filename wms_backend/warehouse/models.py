from django.db import models
from core.models import TenantAwareModel
from accounts.models import User

class Warehouse(TenantAwareModel):
    """
    仓库模型，表示物理仓库
    """
    name = models.CharField(max_length=100, verbose_name="仓库名称")
    code = models.CharField(max_length=50, verbose_name="仓库代码")
    address = models.TextField(blank=True, verbose_name="地址")
    contact_person = models.CharField(max_length=100, blank=True, verbose_name="联系人")
    phone = models.CharField(max_length=50, blank=True, verbose_name="电话")
    email = models.EmailField(blank=True, verbose_name="电子邮件")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")

    class Meta:
        verbose_name = "仓库"
        verbose_name_plural = "仓库"
        db_table = "warehouse_warehouse"
        unique_together = [['tenant', 'code']]

    def __str__(self):
        return self.name

class Zone(models.Model):
    """
    区域模型，表示仓库内的区域
    """
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="zones", verbose_name="仓库")
    name = models.CharField(max_length=100, verbose_name="区域名称")
    code = models.CharField(max_length=50, verbose_name="区域代码")
    description = models.TextField(blank=True, verbose_name="区域描述")
    zone_type = models.CharField(max_length=50, verbose_name="区域类型")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "区域"
        verbose_name_plural = "区域"
        db_table = "warehouse_zone"
        unique_together = [['warehouse', 'code']]

    def __str__(self):
        return f"{self.warehouse.name} - {self.name}"

class Location(models.Model):
    """
    位置模型，表示仓库内的具体位置
    """
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="locations", verbose_name="仓库")
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name="locations", verbose_name="区域")
    name = models.CharField(max_length=100, verbose_name="位置名称")
    code = models.CharField(max_length=50, verbose_name="位置代码")
    barcode = models.CharField(max_length=100, blank=True, verbose_name="条形码")
    location_type = models.CharField(max_length=50, verbose_name="位置类型")
    aisle = models.CharField(max_length=50, blank=True, verbose_name="通道")
    rack = models.CharField(max_length=50, blank=True, verbose_name="货架")
    shelf = models.CharField(max_length=50, blank=True, verbose_name="层")
    bin = models.CharField(max_length=50, blank=True, verbose_name="格")
    max_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="最大承重")
    max_volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="最大体积")
    is_pickable = models.BooleanField(default=True, verbose_name="是否可拣货")
    is_receivable = models.BooleanField(default=True, verbose_name="是否可收货")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "位置"
        verbose_name_plural = "位置"
        db_table = "warehouse_location"
        unique_together = [['warehouse', 'code']]

    def __str__(self):
        return f"{self.warehouse.name} - {self.zone.name} - {self.name}"

class Task(TenantAwareModel):
    """
    任务模型，表示仓库内的各种任务
    """
    TASK_TYPE_CHOICES = (
        ('receiving', '收货'),
        ('putaway', '上架'),
        ('picking', '拣货'),
        ('packing', '打包'),
        ('shipping', '发货'),
        ('stocktake', '盘点'),
        ('transfer', '转移'),
        ('other', '其他'),
    )
    
    PRIORITY_CHOICES = (
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
    )
    
    STATUS_CHOICES = (
        ('pending', '待分配'),
        ('assigned', '已分配'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    )
    
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="tasks", verbose_name="仓库")
    task_type = models.CharField(max_length=50, choices=TASK_TYPE_CHOICES, verbose_name="任务类型")
    reference_type = models.CharField(max_length=100, blank=True, verbose_name="引用类型")
    reference_id = models.IntegerField(null=True, blank=True, verbose_name="引用ID")
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='medium', verbose_name="优先级")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending', verbose_name="状态")
    assigned_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tasks", verbose_name="分配用户")
    start_time = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="结束时间")
    notes = models.TextField(blank=True, verbose_name="备注")

    class Meta:
        verbose_name = "任务"
        verbose_name_plural = "任务"
        db_table = "warehouse_task"

    def __str__(self):
        return f"{self.get_task_type_display()} - {self.id}"

class TaskHistory(models.Model):
    """
    任务历史模型，记录任务状态变更
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="history", verbose_name="任务")
    status = models.CharField(max_length=50, verbose_name="状态")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="用户")
    notes = models.TextField(blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "任务历史"
        verbose_name_plural = "任务历史"
        db_table = "warehouse_task_history"

    def __str__(self):
        return f"{self.task.id} - {self.status}"
