from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Avg, Count, F, Q, Case, When, Value, IntegerField, FloatField
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
import pandas as pd
import json
import csv
import io
from datetime import datetime, timedelta

from .models import (
    Report, ReportSchedule, ReportExecution, 
    Dashboard, DashboardWidget, KPI, KPIValue
)
from .serializers import (
    ReportSerializer, ReportDetailSerializer,
    ReportScheduleSerializer, ReportScheduleDetailSerializer,
    ReportExecutionSerializer, ReportExecutionDetailSerializer,
    DashboardSerializer, DashboardDetailSerializer,
    DashboardWidgetSerializer, KPISerializer, KPIValueSerializer
)
from core.permissions import IsTenantUser
from inventory.models import Product, Inventory, InventoryTransaction, Batch
from warehouse.models import Warehouse, Location
from accounts.models import User

class ReportViewSet(viewsets.ModelViewSet):
    """报表视图集"""
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'report_type', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤条件
        report_type = self.request.query_params.get('report_type')
        is_public = self.request.query_params.get('is_public')
        created_by = self.request.query_params.get('created_by')
        
        if report_type is not None:
            queryset = queryset.filter(report_type=report_type)
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public == 'true')
        if created_by is not None:
            queryset = queryset.filter(created_by=created_by)
        
        # 只返回用户有权限查看的报表
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(
                Q(created_by=user) | 
                Q(is_public=True) | 
                Q(shared_with=user)
            ).distinct()
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ReportDetailSerializer
        return ReportSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """共享报表"""
        report = self.get_object()
        user_ids = request.data.get('user_ids', [])
        
        if not user_ids:
            return Response({'error': '用户ID列表不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证用户是否有权限共享
        if report.created_by != request.user and not request.user.is_staff:
            return Response({'error': '没有权限共享此报表'}, status=status.HTTP_403_FORBIDDEN)
        
        # 添加共享用户
        users = User.objects.filter(id__in=user_ids)
        report.shared_with.add(*users)
        
        serializer = ReportDetailSerializer(report)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unshare(self, request, pk=None):
        """取消共享报表"""
        report = self.get_object()
        user_ids = request.data.get('user_ids', [])
        
        if not user_ids:
            return Response({'error': '用户ID列表不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证用户是否有权限取消共享
        if report.created_by != request.user and not request.user.is_staff:
            return Response({'error': '没有权限取消共享此报表'}, status=status.HTTP_403_FORBIDDEN)
        
        # 移除共享用户
        users = User.objects.filter(id__in=user_ids)
        report.shared_with.remove(*users)
        
        serializer = ReportDetailSerializer(report)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行报表"""
        report = self.get_object()
        parameters = request.data.get('parameters', {})
        
        # 创建报表执行记录
        execution = ReportExecution.objects.create(
            report=report,
            status='running',
            parameters=parameters,
            started_at=timezone.now(),
            created_by=request.user
        )
        
        try:
            # 根据报表类型执行不同的报表生成逻辑
            if report.report_type == 'inventory_status':
                result_data = self._generate_inventory_status_report(parameters)
            elif report.report_type == 'inventory_value':
                result_data = self._generate_inventory_value_report(parameters)
            elif report.report_type == 'inventory_movement':
                result_data = self._generate_inventory_movement_report(parameters)
            elif report.report_type == 'operation_performance':
                result_data = self._generate_operation_performance_report(parameters)
            elif report.report_type == 'user_performance':
                result_data = self._generate_user_performance_report(parameters)
            elif report.report_type == 'custom':
                result_data = self._generate_custom_report(report.config, parameters)
            else:
                raise ValueError(f"不支持的报表类型: {report.report_type}")
            
            # 更新执行记录
            execution.status = 'completed'
            execution.result_data = result_data
            execution.completed_at = timezone.now()
            execution.save()
            
            return Response({
                'execution_id': execution.id,
                'status': 'completed',
                'result_data': result_data
            })
            
        except Exception as e:
            # 记录错误信息
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.completed_at = timezone.now()
            execution.save()
            
            return Response({
                'execution_id': execution.id,
                'status': 'failed',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """导出报表数据"""
        report = self.get_object()
        execution_id = request.query_params.get('execution_id')
        format_type = request.query_params.get('format', 'json')
        
        if not execution_id:
            return Response({'error': '执行ID不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            execution = ReportExecution.objects.get(id=execution_id, report=report)
        except ReportExecution.DoesNotExist:
            return Response({'error': '报表执行记录不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        if execution.status != 'completed':
            return Response({'error': '报表尚未完成执行'}, status=status.HTTP_400_BAD_REQUEST)
        
        result_data = execution.result_data
        
        if format_type == 'csv':
            # 将结果数据转换为CSV格式
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            if 'headers' in result_data:
                writer.writerow(result_data['headers'])
            
            # 写入数据行
            if 'data' in result_data:
                for row in result_data['data']:
                    writer.writerow(row.values() if isinstance(row, dict) else row)
            
            response = Response(output.getvalue())
            response['Content-Type'] = 'text/csv'
            response['Content-Disposition'] = f'attachment; filename="{report.name}_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv"'
            return response
            
        elif format_type == 'excel':
            # 将结果数据转换为Excel格式
            df = pd.DataFrame(result_data.get('data', []))
            excel_file = io.BytesIO()
            df.to_excel(excel_file, index=False)
            excel_file.seek(0)
            
            response = Response(excel_file.read())
            response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response['Content-Disposition'] = f'attachment; filename="{report.name}_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx"'
            return response
            
        else:
            # 默认返回JSON格式
            return Response(result_data)

    def _generate_inventory_status_report(self, parameters):
        """生成库存状态报表"""
        warehouse_id = parameters.get('warehouse_id')
        category_id = parameters.get('category_id')
        include_zero_stock = parameters.get('include_zero_stock', False)
        
        # 构建查询条件
        query = Q()
        if warehouse_id:
            query &= Q(location__warehouse_id=warehouse_id)
        if category_id:
            query &= Q(product__category_id=category_id)
        if not include_zero_stock:
            query &= Q(quantity__gt=0)
        
        # 获取库存数据
        inventory_data = Inventory.objects.filter(query).values(
            'product_id', 'product__name', 'product__sku', 'product__category__name',
            'location__warehouse__name', 'location__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            reserved_quantity=Sum('reserved_quantity'),
            available_quantity=Sum(F('quantity') - F('reserved_quantity'))
        ).order_by('product__name', 'location__name')
        
        # 计算汇总数据
        summary = {
            'total_products': inventory_data.values('product_id').distinct().count(),
            'total_quantity': sum(item['total_quantity'] for item in inventory_data),
            'total_reserved': sum(item['reserved_quantity'] for item in inventory_data),
            'total_available': sum(item['available_quantity'] for item in inventory_data),
        }
        
        # 获取低库存产品
        low_stock_products = Product.objects.filter(
            inventory__quantity__gt=0,
            inventory__quantity__lte=F('min_stock_level')
        ).distinct().count()
        
        # 获取缺货产品
        out_of_stock_products = Product.objects.filter(
            ~Q(inventory__quantity__gt=0) | 
            Q(inventory__quantity=0)
        ).distinct().count()
        
        summary.update({
            'low_stock_products': low_stock_products,
            'out_of_stock_products': out_of_stock_products,
        })
        
        # 格式化数据
        data = []
        for item in inventory_data:
            data.append({
                'product_id': item['product_id'],
                'product_name': item['product__name'],
                'product_sku': item['product__sku'],
                'category': item['product__category__name'],
                'warehouse': item['location__warehouse__name'],
                'location': item['location__name'],
                'total_quantity': item['total_quantity'],
                'reserved_quantity': item['reserved_quantity'],
                'available_quantity': item['available_quantity'],
            })
        
        return {
            'summary': summary,
            'data': data,
            'headers': [
                '产品ID', '产品名称', 'SKU', '类别', '仓库', '位置',
                '总数量', '预留数量', '可用数量'
            ],
            'generated_at': timezone.now().isoformat()
        }

    def _generate_inventory_value_report(self, parameters):
        """生成库存价值报表"""
        warehouse_id = parameters.get('warehouse_id')
        category_id = parameters.get('category_id')
        valuation_method = parameters.get('valuation_method', 'cost_price')
        
        # 构建查询条件
        query = Q()
        if warehouse_id:
            query &= Q(location__warehouse_id=warehouse_id)
        if category_id:
            query &= Q(product__category_id=category_id)
        
        # 获取库存数据
        inventory_data = Inventory.objects.filter(query).values(
            'product_id', 'product__name', 'product__sku', 'product__category__name',
            'product__cost_price', 'product__selling_price',
            'location__warehouse__name'
        ).annotate(
            total_quantity=Sum('quantity')
        ).filter(total_quantity__gt=0).order_by('product__name')
        
        # 计算库存价值
        total_value = 0
        data = []
        
        for item in inventory_data:
            if valuation_method == 'cost_price':
                unit_price = item['product__cost_price'] or 0
            else:  # selling_price
                unit_price = item['product__selling_price'] or 0
            
            value = item['total_quantity'] * unit_price
            total_value += value
            
            data.append({
                'product_id': item['product_id'],
                'product_name': item['product__name'],
                'product_sku': item['product__sku'],
                'category': item['product__category__name'],
                'warehouse': item['location__warehouse__name'],
                'quantity': item['total_quantity'],
                'unit_price': float(unit_price),
                'value': float(value),
            })
        
        # 按类别汇总
        category_summary = {}
        for item in data:
            category = item['category'] or '未分类'
            if category not in category_summary:
                category_summary[category] = 0
            category_summary[category] += item['value']
        
        # 按仓库汇总
        warehouse_summary = {}
        for item in data:
            warehouse = item['warehouse']
            if warehouse not in warehouse_summary:
                warehouse_summary[warehouse] = 0
            warehouse_summary[warehouse] += item['value']
        
        return {
            'summary': {
                'total_value': float(total_value),
                'total_products': len(data),
                'valuation_method': '成本价' if valuation_method == 'cost_price' else '销售价',
                'category_summary': category_summary,
                'warehouse_summary': warehouse_summary,
            },
            'data': data,
            'headers': [
                '产品ID', '产品名称', 'SKU', '类别', '仓库',
                '数量', '单价', '价值'
            ],
            'generated_at': timezone.now().isoformat()
        }

    def _generate_inventory_movement_report(self, parameters):
        """生成库存移动报表"""
        warehouse_id = parameters.get('warehouse_id')
        product_id = parameters.get('product_id')
        start_date = parameters.get('start_date')
        end_date = parameters.get('end_date')
        transaction_type = parameters.get('transaction_type')
        
        # 构建查询条件
        query = Q()
        if warehouse_id:
            query &= Q(inventory__location__warehouse_id=warehouse_id)
        if product_id:
            query &= Q(inventory__product_id=product_id)
        if start_date:
            query &= Q(created_at__gte=start_date)
        if end_date:
            query &= Q(created_at__lte=end_date)
        if transaction_type:
            query &= Q(transaction_type=transaction_type)
        
        # 获取库存交易记录
        transactions = InventoryTransaction.objects.filter(query).select_related(
            'inventory__product', 'inventory__location__warehouse',
            'batch', 'user'
        ).order_by('-created_at')
        
        # 格式化数据
        data = []
        for tx in transactions:
            data.append({
                'id': tx.id,
                'date': tx.created_at.isoformat(),
                'product_id': tx.inventory.product.id,
                'product_name': tx.inventory.product.name,
                'product_sku': tx.inventory.product.sku,
                'warehouse': tx.inventory.location.warehouse.name,
                'location': tx.inventory.location.name,
                'transaction_type': tx.get_transaction_type_display(),
                'quantity': tx.quantity,
                'previous_quantity': tx.previous_quantity,
                'new_quantity': tx.new_quantity,
                'batch_number': tx.batch.batch_number if tx.batch else None,
                'reference_type': tx.reference_type,
                'reference_id': tx.reference_id,
                'user': tx.user.username if tx.user else None,
                'notes': tx.notes,
            })
        
        # 计算汇总数据
        increase_count = sum(1 for tx in transactions if tx.transaction_type == 'increase')
        decrease_count = sum(1 for tx in transactions if tx.transaction_type == 'decrease')
        increase_quantity = sum(tx.quantity for tx in transactions if tx.transaction_type == 'increase')
        decrease_quantity = sum(tx.quantity for tx in transactions if tx.transaction_type == 'decrease')
        
        # 按日期汇总
        date_summary = {}
        for tx in transactions:
            date_str = tx.created_at.date().isoformat()
            if date_str not in date_summary:
                date_summary[date_str] = {'increase': 0, 'decrease': 0}
            
            if tx.transaction_type == 'increase':
                date_summary[date_str]['increase'] += tx.quantity
            else:
                date_summary[date_str]['decrease'] += tx.quantity
        
        # 转换为时间序列数据
        dates = sorted(date_summary.keys())
        time_series = {
            'dates': dates,
            'increase': [date_summary[date]['increase'] for date in dates],
            'decrease': [date_summary[date]['decrease'] for date in dates],
        }
        
        return {
            'summary': {
                'total_transactions': len(data),
                'increase_count': increase_count,
                'decrease_count': decrease_count,
                'increase_quantity': increase_quantity,
                'decrease_quantity': decrease_quantity,
                'net_change': increase_quantity - decrease_quantity,
            },
            'time_series': time_series,
            'data': data,
            'headers': [
                'ID', '日期', '产品ID', '产品名称', 'SKU', '仓库', '位置',
                '交易类型', '数量', '之前数量', '新数量', '批次号',
                '引用类型', '引用ID', '用户', '备注'
            ],
            'generated_at': timezone.now().isoformat()
        }

    def _generate_operation_performance_report(self, parameters):
        """生成操作性能报表"""
        warehouse_id = parameters.get('warehouse_id')
        start_date = parameters.get('start_date')
        end_date = parameters.get('end_date')
        
        # 如果没有指定日期范围，默认为过去30天
        if not start_date:
            start_date = (timezone.now() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = timezone.now().isoformat()
        
        # 构建查询条件
        query = Q(created_at__gte=start_date) & Q(created_at__lte=end_date)
        if warehouse_id:
            query &= Q(inventory__location__warehouse_id=warehouse_id)
        
        # 获取库存交易记录
        transactions = InventoryTransaction.objects.filter(query)
        
        # 按操作类型分组统计
        operation_stats = transactions.values('reference_type').annotate(
            count=Count('id'),
            total_quantity=Sum('quantity')
        ).order_by('reference_type')
        
        # 按日期统计
        date_stats = transactions.extra(
            select={'date': "DATE(created_at)"}
        ).values('date').annotate(
            count=Count('id'),
            increase_count=Count(Case(When(transaction_type='increase', then=1), output_field=IntegerField())),
            decrease_count=Count(Case(When(transaction_type='decrease', then=1), output_field=IntegerField())),
            total_quantity=Sum('quantity')
        ).order_by('date')
        
        # 计算每日平均操作数
        daily_avg = len(date_stats) > 0 and sum(d['count'] for d in date_stats) / len(date_stats) or 0
        
        # 计算高峰时段
        hour_stats = transactions.extra(
            select={'hour': "EXTRACT(HOUR FROM created_at)"}
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('-count')
        
        peak_hours = [int(h['hour']) for h in hour_stats[:3]] if hour_stats else []
        
        # 格式化数据
        operation_data = []
        for stat in operation_stats:
            operation_data.append({
                'reference_type': stat['reference_type'] or '未指定',
                'count': stat['count'],
                'total_quantity': stat['total_quantity'],
                'percentage': round(stat['count'] * 100 / transactions.count(), 2) if transactions.count() > 0 else 0
            })
        
        date_data = []
        for stat in date_stats:
            date_data.append({
                'date': stat['date'].isoformat() if isinstance(stat['date'], datetime.date) else stat['date'],
                'count': stat['count'],
                'increase_count': stat['increase_count'],
                'decrease_count': stat['decrease_count'],
                'total_quantity': stat['total_quantity']
            })
        
        # 计算汇总数据
        summary = {
            'total_operations': transactions.count(),
            'total_quantity_moved': transactions.aggregate(total=Sum('quantity'))['total'] or 0,
            'daily_average_operations': round(daily_avg, 2),
            'peak_hours': peak_hours,
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            }
        }
        
        return {
            'summary': summary,
            'operation_stats': operation_data,
            'date_stats': date_data,
            'headers': [
                '操作类型', '操作次数', '总数量', '百分比'
            ],
            'generated_at': timezone.now().isoformat()
        }

    def _generate_user_performance_report(self, parameters):
        """生成用户绩效报表"""
        warehouse_id = parameters.get('warehouse_id')
        start_date = parameters.get('start_date')
        end_date = parameters.get('end_date')
        
        # 如果没有指定日期范围，默认为过去30天
        if not start_date:
            start_date = (timezone.now() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = timezone.now().isoformat()
        
        # 构建查询条件
        query = Q(created_at__gte=start_date) & Q(created_at__lte=end_date) & ~Q(user=None)
        if warehouse_id:
            query &= Q(inventory__location__warehouse_id=warehouse_id)
        
        # 获取库存交易记录
        transactions = InventoryTransaction.objects.filter(query)
        
        # 按用户分组统计
        user_stats = transactions.values(
            'user__id', 'user__username'
        ).annotate(
            operation_count=Count('id'),
            increase_count=Count(Case(When(transaction_type='increase', then=1), output_field=IntegerField())),
            decrease_count=Count(Case(When(transaction_type='decrease', then=1), output_field=IntegerField())),
            total_quantity=Sum('quantity'),
            avg_quantity=Avg('quantity')
        ).order_by('-operation_count')
        
        # 计算每个用户的操作类型分布
        user_operation_types = {}
        for user_id in set(u['user__id'] for u in user_stats):
            user_operation_types[user_id] = list(
                transactions.filter(user_id=user_id).values('reference_type').annotate(
                    count=Count('id')
                ).order_by('-count')
            )
        
        # 计算每个用户的日均操作数
        user_daily_avg = {}
        for user_id in set(u['user__id'] for u in user_stats):
            user_dates = transactions.filter(user_id=user_id).extra(
                select={'date': "DATE(created_at)"}
            ).values('date').distinct().count()
            
            user_daily_avg[user_id] = user_dates > 0 and transactions.filter(user_id=user_id).count() / user_dates or 0
        
        # 格式化数据
        data = []
        for stat in user_stats:
            user_id = stat['user__id']
            top_operations = user_operation_types.get(user_id, [])
            top_operation_type = top_operations[0]['reference_type'] if top_operations else '无'
            
            data.append({
                'user_id': user_id,
                'username': stat['user__username'],
                'operation_count': stat['operation_count'],
                'increase_count': stat['increase_count'],
                'decrease_count': stat['decrease_count'],
                'total_quantity': stat['total_quantity'],
                'avg_quantity': round(stat['avg_quantity'], 2),
                'daily_avg_operations': round(user_daily_avg.get(user_id, 0), 2),
                'top_operation_type': top_operation_type,
                'percentage': round(stat['operation_count'] * 100 / transactions.count(), 2) if transactions.count() > 0 else 0
            })
        
        # 计算汇总数据
        summary = {
            'total_users': len(data),
            'total_operations': transactions.count(),
            'total_quantity': transactions.aggregate(total=Sum('quantity'))['total'] or 0,
            'avg_operations_per_user': round(transactions.count() / len(data), 2) if len(data) > 0 else 0,
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            }
        }
        
        return {
            'summary': summary,
            'data': data,
            'headers': [
                '用户ID', '用户名', '操作次数', '入库操作', '出库操作',
                '总数量', '平均数量', '日均操作数', '主要操作类型', '百分比'
            ],
            'generated_at': timezone.now().isoformat()
        }

    def _generate_custom_report(self, config, parameters):
        """生成自定义报表"""
        if not config:
            raise ValueError("自定义报表配置不能为空")
        
        report_type = config.get('report_type')
        dimensions = config.get('dimensions', [])
        metrics = config.get('metrics', [])
        filters = config.get('filters', {})
        
        # 合并参数中的过滤条件
        if parameters.get('filters'):
            filters.update(parameters.get('filters'))
        
        # 根据报表类型选择数据源
        if report_type == 'inventory':
            return self._generate_custom_inventory_report(dimensions, metrics, filters)
        elif report_type == 'transactions':
            return self._generate_custom_transaction_report(dimensions, metrics, filters)
        elif report_type == 'products':
            return self._generate_custom_product_report(dimensions, metrics, filters)
        else:
            raise ValueError(f"不支持的自定义报表类型: {report_type}")

    def _generate_custom_inventory_report(self, dimensions, metrics, filters):
        """生成自定义库存报表"""
        # 构建查询条件
        query = Q()
        
        # 应用过滤条件
        if 'warehouse_id' in filters and filters['warehouse_id']:
            query &= Q(location__warehouse_id=filters['warehouse_id'])
        if 'product_id' in filters and filters['product_id']:
            query &= Q(product_id=filters['product_id'])
        if 'category_id' in filters and filters['category_id']:
            query &= Q(product__category_id=filters['category_id'])
        if 'min_quantity' in filters and filters['min_quantity'] is not None:
            query &= Q(quantity__gte=filters['min_quantity'])
        if 'max_quantity' in filters and filters['max_quantity'] is not None:
            query &= Q(quantity__lte=filters['max_quantity'])
        
        # 构建维度字段
        dimension_fields = []
        for dim in dimensions:
            if dim == 'product':
                dimension_fields.extend(['product_id', 'product__name', 'product__sku'])
            elif dim == 'category':
                dimension_fields.extend(['product__category_id', 'product__category__name'])
            elif dim == 'warehouse':
                dimension_fields.extend(['location__warehouse_id', 'location__warehouse__name'])
            elif dim == 'location':
                dimension_fields.extend(['location_id', 'location__name', 'location__code'])
        
        # 构建指标计算
        annotations = {}
        for metric in metrics:
            if metric == 'quantity':
                annotations['total_quantity'] = Sum('quantity')
            elif metric == 'reserved_quantity':
                annotations['total_reserved'] = Sum('reserved_quantity')
            elif metric == 'available_quantity':
                annotations['total_available'] = Sum(F('quantity') - F('reserved_quantity'))
            elif metric == 'value':
                annotations['total_value'] = Sum(F('quantity') * F('product__cost_price'))
        
        # 执行查询
        inventory_data = Inventory.objects.filter(query).values(*dimension_fields).annotate(**annotations)
        
        # 格式化数据
        data = []
        for item in inventory_data:
            row = {}
            
            # 添加维度字段
            for dim in dimensions:
                if dim == 'product':
                    row['product_id'] = item['product_id']
                    row['product_name'] = item['product__name']
                    row['product_sku'] = item['product__sku']
                elif dim == 'category':
                    row['category_id'] = item['product__category_id']
                    row['category_name'] = item['product__category__name']
                elif dim == 'warehouse':
                    row['warehouse_id'] = item['location__warehouse_id']
                    row['warehouse_name'] = item['location__warehouse__name']
                elif dim == 'location':
                    row['location_id'] = item['location_id']
                    row['location_name'] = item['location__name']
                    row['location_code'] = item['location__code']
            
            # 添加指标字段
            for metric in metrics:
                if metric == 'quantity':
                    row['total_quantity'] = item['total_quantity']
                elif metric == 'reserved_quantity':
                    row['total_reserved'] = item['total_reserved']
                elif metric == 'available_quantity':
                    row['total_available'] = item['total_available']
                elif metric == 'value':
                    row['total_value'] = float(item['total_value']) if item['total_value'] else 0
            
            data.append(row)
        
        # 构建表头
        headers = []
        for dim in dimensions:
            if dim == 'product':
                headers.extend(['产品ID', '产品名称', 'SKU'])
            elif dim == 'category':
                headers.extend(['类别ID', '类别名称'])
            elif dim == 'warehouse':
                headers.extend(['仓库ID', '仓库名称'])
            elif dim == 'location':
                headers.extend(['位置ID', '位置名称', '位置编码'])
        
        for metric in metrics:
            if metric == 'quantity':
                headers.append('总数量')
            elif metric == 'reserved_quantity':
                headers.append('预留数量')
            elif metric == 'available_quantity':
                headers.append('可用数量')
            elif metric == 'value':
                headers.append('总价值')
        
        return {
            'data': data,
            'headers': headers,
            'dimensions': dimensions,
            'metrics': metrics,
            'filters': filters,
            'generated_at': timezone.now().isoformat()
        }

    def _generate_custom_transaction_report(self, dimensions, metrics, filters):
        """生成自定义交易报表"""
        # 构建查询条件
        query = Q()
        
        # 应用过滤条件
        if 'start_date' in filters and filters['start_date']:
            query &= Q(created_at__gte=filters['start_date'])
        if 'end_date' in filters and filters['end_date']:
            query &= Q(created_at__lte=filters['end_date'])
        if 'warehouse_id' in filters and filters['warehouse_id']:
            query &= Q(inventory__location__warehouse_id=filters['warehouse_id'])
        if 'product_id' in filters and filters['product_id']:
            query &= Q(inventory__product_id=filters['product_id'])
        if 'transaction_type' in filters and filters['transaction_type']:
            query &= Q(transaction_type=filters['transaction_type'])
        if 'reference_type' in filters and filters['reference_type']:
            query &= Q(reference_type=filters['reference_type'])
        if 'user_id' in filters and filters['user_id']:
            query &= Q(user_id=filters['user_id'])
        
        # 构建维度字段
        dimension_fields = []
        group_by = []
        
        for dim in dimensions:
            if dim == 'date':
                dimension_fields.append('created_at__date')
                group_by.append('created_at__date')
            elif dim == 'product':
                dimension_fields.extend(['inventory__product_id', 'inventory__product__name', 'inventory__product__sku'])
                group_by.append('inventory__product_id')
            elif dim == 'warehouse':
                dimension_fields.extend(['inventory__location__warehouse_id', 'inventory__location__warehouse__name'])
                group_by.append('inventory__location__warehouse_id')
            elif dim == 'location':
                dimension_fields.extend(['inventory__location_id', 'inventory__location__name'])
                group_by.append('inventory__location_id')
            elif dim == 'transaction_type':
                dimension_fields.append('transaction_type')
                group_by.append('transaction_type')
            elif dim == 'reference_type':
                dimension_fields.append('reference_type')
                group_by.append('reference_type')
            elif dim == 'user':
                dimension_fields.extend(['user_id', 'user__username'])
                group_by.append('user_id')
        
        # 构建指标计算
        annotations = {}
        for metric in metrics:
            if metric == 'count':
                annotations['transaction_count'] = Count('id')
            elif metric == 'quantity':
                annotations['total_quantity'] = Sum('quantity')
            elif metric == 'avg_quantity':
                annotations['avg_quantity'] = Avg('quantity')
        
        # 执行查询
        transactions = InventoryTransaction.objects.filter(query)
        
        if group_by:
            transaction_data = transactions.values(*dimension_fields).annotate(**annotations).order_by(*group_by)
        else:
            # 如果没有分组维度，则计算总体指标
            transaction_data = [transactions.aggregate(**annotations)]
            for field in dimension_fields:
                transaction_data[0][field] = None
        
        # 格式化数据
        data = []
        for item in transaction_data:
            row = {}
            
            # 添加维度字段
            for dim in dimensions:
                if dim == 'date':
                    row['date'] = item['created_at__date'].isoformat() if item['created_at__date'] else None
                elif dim == 'product':
                    row['product_id'] = item['inventory__product_id']
                    row['product_name'] = item['inventory__product__name']
                    row['product_sku'] = item['inventory__product__sku']
                elif dim == 'warehouse':
                    row['warehouse_id'] = item['inventory__location__warehouse_id']
                    row['warehouse_name'] = item['inventory__location__warehouse__name']
                elif dim == 'location':
                    row['location_id'] = item['inventory__location_id']
                    row['location_name'] = item['inventory__location__name']
                elif dim == 'transaction_type':
                    row['transaction_type'] = item['transaction_type']
                    row['transaction_type_display'] = dict(InventoryTransaction.transaction_type.field.choices).get(item['transaction_type'], '')
                elif dim == 'reference_type':
                    row['reference_type'] = item['reference_type']
                elif dim == 'user':
                    row['user_id'] = item['user_id']
                    row['username'] = item['user__username']
            
            # 添加指标字段
            for metric in metrics:
                if metric == 'count':
                    row['transaction_count'] = item['transaction_count']
                elif metric == 'quantity':
                    row['total_quantity'] = item['total_quantity']
                elif metric == 'avg_quantity':
                    row['avg_quantity'] = round(item['avg_quantity'], 2) if item['avg_quantity'] else 0
            
            data.append(row)
        
        # 构建表头
        headers = []
        for dim in dimensions:
            if dim == 'date':
                headers.append('日期')
            elif dim == 'product':
                headers.extend(['产品ID', '产品名称', 'SKU'])
            elif dim == 'warehouse':
                headers.extend(['仓库ID', '仓库名称'])
            elif dim == 'location':
                headers.extend(['位置ID', '位置名称'])
            elif dim == 'transaction_type':
                headers.extend(['交易类型', '交易类型显示'])
            elif dim == 'reference_type':
                headers.append('引用类型')
            elif dim == 'user':
                headers.extend(['用户ID', '用户名'])
        
        for metric in metrics:
            if metric == 'count':
                headers.append('交易次数')
            elif metric == 'quantity':
                headers.append('总数量')
            elif metric == 'avg_quantity':
                headers.append('平均数量')
        
        return {
            'data': data,
            'headers': headers,
            'dimensions': dimensions,
            'metrics': metrics,
            'filters': filters,
            'generated_at': timezone.now().isoformat()
        }

    def _generate_custom_product_report(self, dimensions, metrics, filters):
        """生成自定义产品报表"""
        # 构建查询条件
        query = Q()
        
        # 应用过滤条件
        if 'category_id' in filters and filters['category_id']:
            query &= Q(category_id=filters['category_id'])
        if 'is_active' in filters:
            query &= Q(is_active=filters['is_active'])
        if 'min_stock_level' in filters and filters['min_stock_level'] is not None:
            query &= Q(min_stock_level__gte=filters['min_stock_level'])
        if 'has_inventory' in filters and filters['has_inventory']:
            query &= Q(inventory__quantity__gt=0)
        
        # 构建维度字段
        dimension_fields = []
        for dim in dimensions:
            if dim == 'product':
                dimension_fields.extend(['id', 'name', 'sku'])
            elif dim == 'category':
                dimension_fields.extend(['category_id', 'category__name'])
        
        # 构建指标计算
        annotations = {}
        for metric in metrics:
            if metric == 'inventory_quantity':
                annotations['total_quantity'] = Sum('inventory__quantity')
            elif metric == 'available_quantity':
                annotations['available_quantity'] = Sum(F('inventory__quantity') - F('inventory__reserved_quantity'))
            elif metric == 'inventory_value':
                annotations['inventory_value'] = Sum(F('inventory__quantity') * F('cost_price'))
            elif metric == 'low_stock':
                annotations['is_low_stock'] = Case(
                    When(
                        Q(inventory__quantity__gt=0) & Q(inventory__quantity__lte=F('min_stock_level')),
                        then=Value(1)
                    ),
                    default=Value(0),
                    output_field=IntegerField()
                )
        
        # 执行查询
        products = Product.objects.filter(query).values(*dimension_fields).annotate(**annotations)
        
        # 格式化数据
        data = []
        for item in products:
            row = {}
            
            # 添加维度字段
            for dim in dimensions:
                if dim == 'product':
                    row['product_id'] = item['id']
                    row['product_name'] = item['name']
                    row['product_sku'] = item['sku']
                elif dim == 'category':
                    row['category_id'] = item['category_id']
                    row['category_name'] = item['category__name']
            
            # 添加指标字段
            for metric in metrics:
                if metric == 'inventory_quantity':
                    row['total_quantity'] = item['total_quantity'] or 0
                elif metric == 'available_quantity':
                    row['available_quantity'] = item['available_quantity'] or 0
                elif metric == 'inventory_value':
                    row['inventory_value'] = float(item['inventory_value']) if item['inventory_value'] else 0
                elif metric == 'low_stock':
                    row['is_low_stock'] = bool(item['is_low_stock'])
            
            data.append(row)
        
        # 构建表头
        headers = []
        for dim in dimensions:
            if dim == 'product':
                headers.extend(['产品ID', '产品名称', 'SKU'])
            elif dim == 'category':
                headers.extend(['类别ID', '类别名称'])
        
        for metric in metrics:
            if metric == 'inventory_quantity':
                headers.append('总库存数量')
            elif metric == 'available_quantity':
                headers.append('可用库存数量')
            elif metric == 'inventory_value':
                headers.append('库存价值')
            elif metric == 'low_stock':
                headers.append('是否低库存')
        
        return {
            'data': data,
            'headers': headers,
            'dimensions': dimensions,
            'metrics': metrics,
            'filters': filters,
            'generated_at': timezone.now().isoformat()
        }

class ReportScheduleViewSet(viewsets.ModelViewSet):
    """报表计划视图集"""
    queryset = ReportSchedule.objects.all()
    serializer_class = ReportScheduleSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'report__name']
    ordering_fields = ['name', 'frequency', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤条件
        report_id = self.request.query_params.get('report_id')
        frequency = self.request.query_params.get('frequency')
        is_active = self.request.query_params.get('is_active')
        
        if report_id is not None:
            queryset = queryset.filter(report_id=report_id)
        if frequency is not None:
            queryset = queryset.filter(frequency=frequency)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        
        # 只返回用户有权限查看的报表计划
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(
                Q(report__created_by=user) | 
                Q(report__is_public=True) | 
                Q(report__shared_with=user)
            ).distinct()
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ReportScheduleDetailSerializer
        return ReportScheduleSerializer

    @action(detail=True, methods=['post'])
    def add_recipients(self, request, pk=None):
        """添加接收者"""
        schedule = self.get_object()
        user_ids = request.data.get('user_ids', [])
        
        if not user_ids:
            return Response({'error': '用户ID列表不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证用户是否有权限添加接收者
        if schedule.report.created_by != request.user and not request.user.is_staff:
            return Response({'error': '没有权限修改此报表计划'}, status=status.HTTP_403_FORBIDDEN)
        
        # 添加接收者
        users = User.objects.filter(id__in=user_ids)
        schedule.recipients.add(*users)
        
        serializer = ReportScheduleDetailSerializer(schedule)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def remove_recipients(self, request, pk=None):
        """移除接收者"""
        schedule = self.get_object()
        user_ids = request.data.get('user_ids', [])
        
        if not user_ids:
            return Response({'error': '用户ID列表不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证用户是否有权限移除接收者
        if schedule.report.created_by != request.user and not request.user.is_staff:
            return Response({'error': '没有权限修改此报表计划'}, status=status.HTTP_403_FORBIDDEN)
        
        # 移除接收者
        users = User.objects.filter(id__in=user_ids)
        schedule.recipients.remove(*users)
        
        serializer = ReportScheduleDetailSerializer(schedule)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def execute_now(self, request, pk=None):
        """立即执行报表计划"""
        schedule = self.get_object()
        
        # 创建报表执行记录
        execution = ReportExecution.objects.create(
            report=schedule.report,
            schedule=schedule,
            status='running',
            parameters=schedule.report.config,
            started_at=timezone.now(),
            created_by=request.user
        )
        
        try:
            # 根据报表类型执行不同的报表生成逻辑
            report_view = ReportViewSet()
            
            if schedule.report.report_type == 'inventory_status':
                result_data = report_view._generate_inventory_status_report(schedule.report.config or {})
            elif schedule.report.report_type == 'inventory_value':
                result_data = report_view._generate_inventory_value_report(schedule.report.config or {})
            elif schedule.report.report_type == 'inventory_movement':
                result_data = report_view._generate_inventory_movement_report(schedule.report.config or {})
            elif schedule.report.report_type == 'operation_performance':
                result_data = report_view._generate_operation_performance_report(schedule.report.config or {})
            elif schedule.report.report_type == 'user_performance':
                result_data = report_view._generate_user_performance_report(schedule.report.config or {})
            elif schedule.report.report_type == 'custom':
                result_data = report_view._generate_custom_report(schedule.report.config or {}, {})
            else:
                raise ValueError(f"不支持的报表类型: {schedule.report.report_type}")
            
            # 更新执行记录
            execution.status = 'completed'
            execution.result_data = result_data
            execution.completed_at = timezone.now()
            execution.save()
            
            # 更新计划的最后运行时间
            schedule.last_run = timezone.now()
            schedule.save()
            
            return Response({
                'execution_id': execution.id,
                'status': 'completed',
                'message': '报表计划执行成功'
            })
            
        except Exception as e:
            # 记录错误信息
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.completed_at = timezone.now()
            execution.save()
            
            return Response({
                'execution_id': execution.id,
                'status': 'failed',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ReportExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """报表执行记录视图集"""
    queryset = ReportExecution.objects.all()
    serializer_class = ReportExecutionSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['report__name', 'status']
    ordering_fields = ['created_at', 'started_at', 'completed_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤条件
        report_id = self.request.query_params.get('report_id')
        schedule_id = self.request.query_params.get('schedule_id')
        status_param = self.request.query_params.get('status')
        created_by = self.request.query_params.get('created_by')
        
        if report_id is not None:
            queryset = queryset.filter(report_id=report_id)
        if schedule_id is not None:
            queryset = queryset.filter(schedule_id=schedule_id)
        if status_param is not None:
            queryset = queryset.filter(status=status_param)
        if created_by is not None:
            queryset = queryset.filter(created_by=created_by)
        
        # 只返回用户有权限查看的报表执行记录
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(
                Q(report__created_by=user) | 
                Q(report__is_public=True) | 
                Q(report__shared_with=user) |
                Q(created_by=user)
            ).distinct()
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ReportExecutionDetailSerializer
        return ReportExecutionSerializer

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载报表执行结果"""
        execution = self.get_object()
        format_type = request.query_params.get('format', 'json')
        
        if execution.status != 'completed':
            return Response({'error': '报表尚未完成执行'}, status=status.HTTP_400_BAD_REQUEST)
        
        result_data = execution.result_data
        
        if format_type == 'csv':
            # 将结果数据转换为CSV格式
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            if 'headers' in result_data:
                writer.writerow(result_data['headers'])
            
            # 写入数据行
            if 'data' in result_data:
                for row in result_data['data']:
                    writer.writerow(row.values() if isinstance(row, dict) else row)
            
            response = Response(output.getvalue())
            response['Content-Type'] = 'text/csv'
            response['Content-Disposition'] = f'attachment; filename="{execution.report.name}_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv"'
            return response
            
        elif format_type == 'excel':
            # 将结果数据转换为Excel格式
            df = pd.DataFrame(result_data.get('data', []))
            excel_file = io.BytesIO()
            df.to_excel(excel_file, index=False)
            excel_file.seek(0)
            
            response = Response(excel_file.read())
            response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response['Content-Disposition'] = f'attachment; filename="{execution.report.name}_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx"'
            return response
            
        else:
            # 默认返回JSON格式
            return Response(result_data)

class DashboardViewSet(viewsets.ModelViewSet):
    """仪表板视图集"""
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤条件
        is_public = self.request.query_params.get('is_public')
        created_by = self.request.query_params.get('created_by')
        
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public == 'true')
        if created_by is not None:
            queryset = queryset.filter(created_by=created_by)
        
        # 只返回用户有权限查看的仪表板
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(
                Q(created_by=user) | 
                Q(is_public=True) | 
                Q(shared_with=user)
            ).distinct()
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DashboardDetailSerializer
        return DashboardSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """共享仪表板"""
        dashboard = self.get_object()
        user_ids = request.data.get('user_ids', [])
        
        if not user_ids:
            return Response({'error': '用户ID列表不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证用户是否有权限共享
        if dashboard.created_by != request.user and not request.user.is_staff:
            return Response({'error': '没有权限共享此仪表板'}, status=status.HTTP_403_FORBIDDEN)
        
        # 添加共享用户
        users = User.objects.filter(id__in=user_ids)
        dashboard.shared_with.add(*users)
        
        serializer = DashboardDetailSerializer(dashboard)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unshare(self, request, pk=None):
        """取消共享仪表板"""
        dashboard = self.get_object()
        user_ids = request.data.get('user_ids', [])
        
        if not user_ids:
            return Response({'error': '用户ID列表不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证用户是否有权限取消共享
        if dashboard.created_by != request.user and not request.user.is_staff:
            return Response({'error': '没有权限取消共享此仪表板'}, status=status.HTTP_403_FORBIDDEN)
        
        # 移除共享用户
        users = User.objects.filter(id__in=user_ids)
        dashboard.shared_with.remove(*users)
        
        serializer = DashboardDetailSerializer(dashboard)
        return Response(serializer.data)

class DashboardWidgetViewSet(viewsets.ModelViewSet):
    """仪表板小部件视图集"""
    queryset = DashboardWidget.objects.all()
    serializer_class = DashboardWidgetSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'data_source']
    ordering_fields = ['title', 'widget_type', 'created_at', 'updated_at']
    ordering = ['dashboard', 'position_y', 'position_x']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤条件
        dashboard_id = self.request.query_params.get('dashboard_id')
        widget_type = self.request.query_params.get('widget_type')
        data_source = self.request.query_params.get('data_source')
        
        if dashboard_id is not None:
            queryset = queryset.filter(dashboard_id=dashboard_id)
        if widget_type is not None:
            queryset = queryset.filter(widget_type=widget_type)
        if data_source is not None:
            queryset = queryset.filter(data_source=data_source)
        
        # 只返回用户有权限查看的仪表板小部件
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(
                Q(dashboard__created_by=user) | 
                Q(dashboard__is_public=True) | 
                Q(dashboard__shared_with=user)
            ).distinct()
        
        return queryset

    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        """获取小部件数据"""
        widget = self.get_object()
        
        try:
            # 根据数据源获取数据
            if widget.data_source == 'inventory_summary':
                data = self._get_inventory_summary_data(widget.config)
            elif widget.data_source == 'inventory_value':
                data = self._get_inventory_value_data(widget.config)
            elif widget.data_source == 'inventory_movement':
                data = self._get_inventory_movement_data(widget.config)
            elif widget.data_source == 'low_stock':
                data = self._get_low_stock_data(widget.config)
            elif widget.data_source == 'operation_performance':
                data = self._get_operation_performance_data(widget.config)
            elif widget.data_source == 'user_performance':
                data = self._get_user_performance_data(widget.config)
            elif widget.data_source == 'kpi':
                data = self._get_kpi_data(widget.config)
            else:
                return Response({'error': f"不支持的数据源: {widget.data_source}"}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_inventory_summary_data(self, config):
        """获取库存概览数据"""
        warehouse_id = config.get('warehouse_id') if config else None
        
        # 构建查询条件
        query = Q()
        if warehouse_id:
            query &= Q(location__warehouse_id=warehouse_id)
        
        # 获取库存数据
        total_products = Product.objects.count()
        total_quantity = Inventory.objects.filter(query).aggregate(total=Sum('quantity'))['total'] or 0
        
        # 获取低库存产品
        low_stock_products = Product.objects.filter(
            inventory__quantity__gt=0,
            inventory__quantity__lte=F('min_stock_level')
        ).distinct().count()
        
        # 获取缺货产品
        out_of_stock_products = Product.objects.filter(
            ~Q(inventory__quantity__gt=0) | 
            Q(inventory__quantity=0)
        ).distinct().count()
        
        return {
            'total_products': total_products,
            'total_quantity': total_quantity,
            'low_stock_products': low_stock_products,
            'out_of_stock_products': out_of_stock_products,
            'generated_at': timezone.now().isoformat()
        }

    def _get_inventory_value_data(self, config):
        """获取库存价值数据"""
        warehouse_id = config.get('warehouse_id') if config else None
        valuation_method = config.get('valuation_method', 'cost_price') if config else 'cost_price'
        
        # 构建查询条件
        query = Q()
        if warehouse_id:
            query &= Q(location__warehouse_id=warehouse_id)
        
        # 获取库存数据
        inventory_data = Inventory.objects.filter(query).values(
            'product__category__name'
        ).annotate(
            total_quantity=Sum('quantity')
        ).filter(total_quantity__gt=0)
        
        # 计算库存价值
        category_values = {}
        total_value = 0
        
        for item in inventory_data:
            category = item['product__category__name'] or '未分类'
            
            # 获取该类别下的产品库存价值
            category_inventory = Inventory.objects.filter(
                query, 
                product__category__name=item['product__category__name']
            ).select_related('product')
            
            category_value = 0
            for inv in category_inventory:
                if valuation_method == 'cost_price':
                    unit_price = inv.product.cost_price or 0
                else:  # selling_price
                    unit_price = inv.product.selling_price or 0
                
                category_value += inv.quantity * unit_price
            
            category_values[category] = float(category_value)
            total_value += category_value
        
        # 转换为图表数据格式
        chart_data = [
            {'name': category, 'value': value}
            for category, value in category_values.items()
        ]
        
        return {
            'total_value': float(total_value),
            'valuation_method': valuation_method,
            'chart_data': chart_data,
            'generated_at': timezone.now().isoformat()
        }

    def _get_inventory_movement_data(self, config):
        """获取库存移动数据"""
        days = config.get('days', 30) if config else 30
        warehouse_id = config.get('warehouse_id') if config else None
        
        # 计算日期范围
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 构建查询条件
        query = Q(created_at__date__gte=start_date) & Q(created_at__date__lte=end_date)
        if warehouse_id:
            query &= Q(inventory__location__warehouse_id=warehouse_id)
        
        # 获取库存交易记录
        transactions = InventoryTransaction.objects.filter(query)
        
        # 按日期和交易类型分组统计
        date_stats = {}
        for tx in transactions:
            date_str = tx.created_at.date().isoformat()
            if date_str not in date_stats:
                date_stats[date_str] = {'increase': 0, 'decrease': 0}
            
            if tx.transaction_type == 'increase':
                date_stats[date_str]['increase'] += tx.quantity
            else:
                date_stats[date_str]['decrease'] += tx.quantity
        
        # 确保所有日期都有数据
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            if date_str not in date_stats:
                date_stats[date_str] = {'increase': 0, 'decrease': 0}
            current_date += timedelta(days=1)
        
        # 转换为时间序列数据
        dates = sorted(date_stats.keys())
        time_series = {
            'dates': dates,
            'increase': [date_stats[date]['increase'] for date in dates],
            'decrease': [date_stats[date]['decrease'] for date in dates],
        }
        
        return {
            'time_series': time_series,
            'summary': {
                'total_increase': sum(time_series['increase']),
                'total_decrease': sum(time_series['decrease']),
                'net_change': sum(time_series['increase']) - sum(time_series['decrease']),
            },
            'generated_at': timezone.now().isoformat()
        }

    def _get_low_stock_data(self, config):
        """获取低库存数据"""
        limit = config.get('limit', 10) if config else 10
        include_zero_stock = config.get('include_zero_stock', True) if config else True
        
        # 构建查询条件
        if include_zero_stock:
            query = Q(inventory__quantity__lte=F('min_stock_level'))
        else:
            query = Q(inventory__quantity__gt=0) & Q(inventory__quantity__lte=F('min_stock_level'))
        
        # 获取低库存产品
        low_stock_products = Product.objects.filter(query).distinct().annotate(
            total_quantity=Sum('inventory__quantity'),
            available_quantity=Sum(F('inventory__quantity') - F('inventory__reserved_quantity'))
        ).order_by('available_quantity')[:limit]
        
        # 格式化数据
        data = []
        for product in low_stock_products:
            data.append({
                'product_id': product.id,
                'product_name': product.name,
                'product_sku': product.sku,
                'category': product.category.name if product.category else '未分类',
                'min_stock_level': product.min_stock_level,
                'reorder_point': product.reorder_point,
                'total_quantity': product.total_quantity or 0,
                'available_quantity': product.available_quantity or 0,
            })
        
        return {
            'data': data,
            'count': len(data),
            'generated_at': timezone.now().isoformat()
        }

    def _get_operation_performance_data(self, config):
        """获取操作性能数据"""
        days = config.get('days', 30) if config else 30
        warehouse_id = config.get('warehouse_id') if config else None
        
        # 计算日期范围
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 构建查询条件
        query = Q(created_at__date__gte=start_date) & Q(created_at__date__lte=end_date)
        if warehouse_id:
            query &= Q(inventory__location__warehouse_id=warehouse_id)
        
        # 获取库存交易记录
        transactions = InventoryTransaction.objects.filter(query)
        
        # 按操作类型分组统计
        operation_stats = transactions.values('reference_type').annotate(
            count=Count('id'),
            total_quantity=Sum('quantity')
        ).order_by('-count')
        
        # 格式化数据
        operation_data = []
        for stat in operation_stats:
            operation_data.append({
                'reference_type': stat['reference_type'] or '未指定',
                'count': stat['count'],
                'total_quantity': stat['total_quantity'],
                'percentage': round(stat['count'] * 100 / transactions.count(), 2) if transactions.count() > 0 else 0
            })
        
        # 按日期统计
        date_stats = {}
        for tx in transactions:
            date_str = tx.created_at.date().isoformat()
            if date_str not in date_stats:
                date_stats[date_str] = {'count': 0}
            
            date_stats[date_str]['count'] += 1
        
        # 确保所有日期都有数据
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            if date_str not in date_stats:
                date_stats[date_str] = {'count': 0}
            current_date += timedelta(days=1)
        
        # 转换为时间序列数据
        dates = sorted(date_stats.keys())
        time_series = {
            'dates': dates,
            'counts': [date_stats[date]['count'] for date in dates],
        }
        
        return {
            'operation_stats': operation_data,
            'time_series': time_series,
            'summary': {
                'total_operations': transactions.count(),
                'daily_average': round(transactions.count() / days, 2),
            },
            'generated_at': timezone.now().isoformat()
        }

    def _get_user_performance_data(self, config):
        """获取用户绩效数据"""
        days = config.get('days', 30) if config else 30
        limit = config.get('limit', 5) if config else 5
        
        # 计算日期范围
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 构建查询条件
        query = Q(created_at__date__gte=start_date) & Q(created_at__date__lte=end_date) & ~Q(user=None)
        
        # 获取库存交易记录
        transactions = InventoryTransaction.objects.filter(query)
        
        # 按用户分组统计
        user_stats = transactions.values(
            'user__id', 'user__username'
        ).annotate(
            operation_count=Count('id'),
            total_quantity=Sum('quantity')
        ).order_by('-operation_count')[:limit]
        
        # 格式化数据
        data = []
        for stat in user_stats:
            data.append({
                'user_id': stat['user__id'],
                'username': stat['user__username'],
                'operation_count': stat['operation_count'],
                'total_quantity': stat['total_quantity'],
                'percentage': round(stat['operation_count'] * 100 / transactions.count(), 2) if transactions.count() > 0 else 0
            })
        
        return {
            'data': data,
            'summary': {
                'total_users': User.objects.count(),
                'active_users': transactions.values('user').distinct().count(),
                'total_operations': transactions.count(),
            },
            'generated_at': timezone.now().isoformat()
        }

    def _get_kpi_data(self, config):
        """获取KPI数据"""
        kpi_id = config.get('kpi_id') if config else None
        days = config.get('days', 30) if config else 30
        
        if not kpi_id:
            return {'error': 'KPI ID不能为空'}
        
        try:
            kpi = KPI.objects.get(id=kpi_id)
        except KPI.DoesNotExist:
            return {'error': 'KPI不存在'}
        
        # 计算日期范围
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 获取KPI值记录
        kpi_values = KPIValue.objects.filter(
            kpi=kpi,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # 格式化数据
        dates = []
        values = []
        
        for kv in kpi_values:
            dates.append(kv.date.isoformat())
            values.append(kv.value)
        
        # 计算统计数据
        if values:
            avg_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)
            latest_value = values[-1] if values else None
        else:
            avg_value = min_value = max_value = latest_value = None
        
        return {
            'kpi': {
                'id': kpi.id,
                'name': kpi.name,
                'description': kpi.description,
                'category': kpi.category,
                'unit': kpi.unit,
                'target_value': kpi.target_value,
            },
            'time_series': {
                'dates': dates,
                'values': values,
            },
            'stats': {
                'avg_value': avg_value,
                'min_value': min_value,
                'max_value': max_value,
                'latest_value': latest_value,
            },
            'generated_at': timezone.now().isoformat()
        }

class KPIViewSet(viewsets.ModelViewSet):
    """KPI视图集"""
    queryset = KPI.objects.all()
    serializer_class = KPISerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['name', 'category', 'created_at', 'updated_at']
    ordering = ['category', 'name']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤条件
        category = self.request.query_params.get('category')
        is_active = self.request.query_params.get('is_active')
        
        if category is not None:
            queryset = queryset.filter(category=category)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        
        return queryset

    @action(detail=True, methods=['get'])
    def values(self, request, pk=None):
        """获取KPI值记录"""
        kpi = self.get_object()
        
        # 过滤条件
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        warehouse_id = request.query_params.get('warehouse_id')
        user_id = request.query_params.get('user_id')
        
        # 构建查询条件
        query = Q(kpi=kpi)
        
        if start_date:
            query &= Q(date__gte=start_date)
        if end_date:
            query &= Q(date__lte=end_date)
        if warehouse_id:
            query &= Q(warehouse_id=warehouse_id)
        if user_id:
            query &= Q(user_id=user_id)
        
        # 获取KPI值记录
        kpi_values = KPIValue.objects.filter(query).order_by('date')
        serializer = KPIValueSerializer(kpi_values, many=True)
        
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_value(self, request, pk=None):
        """添加KPI值记录"""
        kpi = self.get_object()
        
        # 验证参数
        date = request.data.get('date')
        value = request.data.get('value')
        warehouse_id = request.data.get('warehouse_id')
        user_id = request.data.get('user_id')
        
        if not date:
            return Response({'error': '日期不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            value = float(value)
        except (TypeError, ValueError):
            return Response({'error': '值必须是数字'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建KPI值记录
        kpi_value = KPIValue.objects.create(
            kpi=kpi,
            date=date,
            value=value,
            warehouse_id=warehouse_id,
            user_id=user_id
        )
        
        serializer = KPIValueSerializer(kpi_value)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class KPIValueViewSet(viewsets.ModelViewSet):
    """KPI值记录视图集"""
    queryset = KPIValue.objects.all()
    serializer_class = KPIValueSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['kpi__name', 'warehouse__name', 'user__username']
    ordering_fields = ['date', 'value', 'created_at']
    ordering = ['-date']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤条件
        kpi_id = self.request.query_params.get('kpi_id')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        warehouse_id = self.request.query_params.get('warehouse_id')
        user_id = self.request.query_params.get('user_id')
        
        if kpi_id is not None:
            queryset = queryset.filter(kpi_id=kpi_id)
        if start_date is not None:
            queryset = queryset.filter(date__gte=start_date)
        if end_date is not None:
            queryset = queryset.filter(date__lte=end_date)
        if warehouse_id is not None:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        if user_id is not None:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset
