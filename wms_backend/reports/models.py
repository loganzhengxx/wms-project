from django.db import models
from django.utils import timezone
from core.models import TenantAwareModel
from accounts.models import User

class Report(TenantAwareModel):
    """报表模型"""
    name = models.CharField(max_length=255, verbose_name="报表名称")
    description = models.TextField(verbose_name="描述", blank=True, null=True)
    report_type = models.CharField(max_length=50, choices=[
        ('inventory_status', '库存状态'),
        ('inventory_value', '库存价值'),
        ('inventory_movement', '库存移动'),
        ('operation_performance', '操作性能'),
        ('user_performance', '用户绩效'),
        ('custom', '自定义报表'),
    ], verbose_name="报表类型")
    
    # 自定义报表配置
    config = models.JSONField(verbose_name="配置", blank=True, null=True)
    
    # 报表权限
    is_public = models.BooleanField(default=False, verbose_name="是否公开")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_reports', verbose_name="创建人")
    shared_with = models.ManyToManyField(User, related_name='shared_reports', blank=True, verbose_name="共享用户")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "报表"
        verbose_name_plural = "报表"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report_type']),
            models.Index(fields=['created_by']),
        ]

class ReportSchedule(TenantAwareModel):
    """报表计划模型"""
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='schedules', verbose_name="报表")
    name = models.CharField(max_length=255, verbose_name="计划名称")
    frequency = models.CharField(max_length=20, choices=[
        ('daily', '每日'),
        ('weekly', '每周'),
        ('monthly', '每月'),
        ('quarterly', '每季度'),
    ], verbose_name="频率")
    day_of_week = models.IntegerField(blank=True, null=True, verbose_name="星期几")
    day_of_month = models.IntegerField(blank=True, null=True, verbose_name="每月第几天")
    time_of_day = models.TimeField(verbose_name="时间")
    
    # 接收者
    recipients = models.ManyToManyField(User, related_name='report_schedules', verbose_name="接收者")
    email_subject = models.CharField(max_length=255, verbose_name="邮件主题")
    email_body = models.TextField(verbose_name="邮件内容", blank=True, null=True)
    
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    last_run = models.DateTimeField(blank=True, null=True, verbose_name="上次运行时间")
    next_run = models.DateTimeField(blank=True, null=True, verbose_name="下次运行时间")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    def __str__(self):
        return f"{self.report.name} - {self.name}"
    
    class Meta:
        verbose_name = "报表计划"
        verbose_name_plural = "报表计划"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['frequency']),
            models.Index(fields=['is_active']),
        ]

class ReportExecution(TenantAwareModel):
    """报表执行记录模型"""
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='executions', verbose_name="报表")
    schedule = models.ForeignKey(ReportSchedule, on_delete=models.SET_NULL, blank=True, null=True, related_name='executions', verbose_name="计划")
    
    status = models.CharField(max_length=20, choices=[
        ('pending', '待处理'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ], default='pending', verbose_name="状态")
    
    parameters = models.JSONField(verbose_name="参数", blank=True, null=True)
    result_data = models.JSONField(verbose_name="结果数据", blank=True, null=True)
    error_message = models.TextField(verbose_name="错误信息", blank=True, null=True)
    
    started_at = models.DateTimeField(blank=True, null=True, verbose_name="开始时间")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="完成时间")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='report_executions', verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    def __str__(self):
        return f"{self.report.name} - {self.created_at}"
    
    class Meta:
        verbose_name = "报表执行记录"
        verbose_name_plural = "报表执行记录"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]

class Dashboard(TenantAwareModel):
    """仪表板模型"""
    name = models.CharField(max_length=255, verbose_name="仪表板名称")
    description = models.TextField(verbose_name="描述", blank=True, null=True)
    layout = models.JSONField(verbose_name="布局", blank=True, null=True)
    
    # 仪表板权限
    is_public = models.BooleanField(default=False, verbose_name="是否公开")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_dashboards', verbose_name="创建人")
    shared_with = models.ManyToManyField(User, related_name='shared_dashboards', blank=True, verbose_name="共享用户")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "仪表板"
        verbose_name_plural = "仪表板"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_by']),
        ]

class DashboardWidget(TenantAwareModel):
    """仪表板小部件模型"""
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widgets', verbose_name="仪表板")
    title = models.CharField(max_length=255, verbose_name="标题")
    widget_type = models.CharField(max_length=50, choices=[
        ('chart', '图表'),
        ('table', '表格'),
        ('metric', '指标'),
        ('list', '列表'),
    ], verbose_name="小部件类型")
    
    # 数据源配置
    data_source = models.CharField(max_length=50, verbose_name="数据源")
    config = models.JSONField(verbose_name="配置", blank=True, null=True)
    
    # 位置和大小
    position_x = models.IntegerField(default=0, verbose_name="X位置")
    position_y = models.IntegerField(default=0, verbose_name="Y位置")
    width = models.IntegerField(default=1, verbose_name="宽度")
    height = models.IntegerField(default=1, verbose_name="高度")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    def __str__(self):
        return f"{self.dashboard.name} - {self.title}"
    
    class Meta:
        verbose_name = "仪表板小部件"
        verbose_name_plural = "仪表板小部件"
        ordering = ['dashboard', 'position_y', 'position_x']
        indexes = [
            models.Index(fields=['widget_type']),
            models.Index(fields=['data_source']),
        ]

class KPI(TenantAwareModel):
    """关键绩效指标模型"""
    name = models.CharField(max_length=255, verbose_name="KPI名称")
    description = models.TextField(verbose_name="描述", blank=True, null=True)
    category = models.CharField(max_length=50, choices=[
        ('inventory', '库存'),
        ('operations', '操作'),
        ('efficiency', '效率'),
        ('quality', '质量'),
        ('financial', '财务'),
    ], verbose_name="类别")
    
    # 计算方法
    calculation_method = models.TextField(verbose_name="计算方法")
    unit = models.CharField(max_length=50, verbose_name="单位", blank=True, null=True)
    
    # 目标值
    target_value = models.FloatField(verbose_name="目标值", blank=True, null=True)
    min_value = models.FloatField(verbose_name="最小值", blank=True, null=True)
    max_value = models.FloatField(verbose_name="最大值", blank=True, null=True)
    
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "关键绩效指标"
        verbose_name_plural = "关键绩效指标"
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]

class KPIValue(TenantAwareModel):
    """KPI值记录模型"""
    kpi = models.ForeignKey(KPI, on_delete=models.CASCADE, related_name='values', verbose_name="KPI")
    date = models.DateField(verbose_name="日期")
    value = models.FloatField(verbose_name="值")
    
    # 可选的维度
    warehouse = models.ForeignKey('warehouse.Warehouse', on_delete=models.CASCADE, blank=True, null=True, verbose_name="仓库")
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, verbose_name="用户")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    def __str__(self):
        return f"{self.kpi.name} - {self.date} - {self.value}"
    
    class Meta:
        verbose_name = "KPI值记录"
        verbose_name_plural = "KPI值记录"
        ordering = ['-date', 'kpi']
        indexes = [
            models.Index(fields=['kpi', '-date']),
            models.Index(fields=['warehouse']),
            models.Index(fields=['user']),
        ]
