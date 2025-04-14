from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, F, Q, Count, Case, When, IntegerField
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import (
    Product, ProductCategory, ProductAttribute, ProductAttributeValue, 
    ProductImage, Batch, SerialNumber, Inventory, BatchInventory,
    InventoryTransaction, InventoryCount, InventoryCountItem, InventoryAlert
)
from .serializers import (
    ProductSerializer, ProductDetailSerializer, ProductCategorySerializer,
    ProductAttributeSerializer, ProductAttributeValueSerializer, ProductImageSerializer,
    BatchSerializer, SerialNumberSerializer, InventorySerializer, BatchInventorySerializer,
    InventoryTransactionSerializer, InventoryCountSerializer, InventoryCountDetailSerializer,
    InventoryCountItemSerializer, InventoryAlertSerializer
)
from core.permissions import IsTenantUser
from warehouse.models import Location

class ProductCategoryViewSet(viewsets.ModelViewSet):
    """产品类别视图集"""
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        # 过滤条件
        is_active = self.request.query_params.get('is_active')
        parent = self.request.query_params.get('parent')
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        if parent is not None:
            if parent == 'null':
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent=parent)
        
        return queryset

class ProductAttributeViewSet(viewsets.ModelViewSet):
    """产品属性视图集"""
    queryset = ProductAttribute.objects.all()
    serializer_class = ProductAttributeSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        # 过滤条件
        is_active = self.request.query_params.get('is_active')
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        
        return queryset

class ProductViewSet(viewsets.ModelViewSet):
    """产品视图集"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'sku', 'barcode', 'description']
    ordering_fields = ['name', 'sku', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 添加库存数量统计
        queryset = queryset.annotate(
            total_quantity=Sum('inventory__quantity', default=0),
            available_quantity=Sum(
                F('inventory__quantity') - F('inventory__reserved_quantity'),
                default=0
            )
        )
        
        # 过滤条件
        category = self.request.query_params.get('category')
        is_active = self.request.query_params.get('is_active')
        low_stock = self.request.query_params.get('low_stock')
        out_of_stock = self.request.query_params.get('out_of_stock')
        
        if category is not None:
            queryset = queryset.filter(category=category)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        if low_stock is not None and low_stock.lower() == 'true':
            queryset = queryset.filter(
                available_quantity__gt=0,
                available_quantity__lte=F('min_stock_level')
            )
        if out_of_stock is not None and out_of_stock.lower() == 'true':
            queryset = queryset.filter(available_quantity__lte=0)
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer

    @action(detail=True, methods=['post'])
    def add_attribute(self, request, pk=None):
        """添加产品属性"""
        product = self.get_object()
        serializer = ProductAttributeValueSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None):
        """上传产品图片"""
        product = self.get_object()
        serializer = ProductImageSerializer(data=request.data)
        
        if serializer.is_valid():
            # 如果设置为主图，先将其他图片设为非主图
            if serializer.validated_data.get('is_primary', False):
                ProductImage.objects.filter(product=product, is_primary=True).update(is_primary=False)
            
            serializer.save(product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """获取产品库存信息"""
        product = self.get_object()
        inventory = Inventory.objects.filter(product=product)
        
        # 添加可用数量计算
        inventory = inventory.annotate(
            available_quantity=F('quantity') - F('reserved_quantity')
        )
        
        serializer = InventorySerializer(inventory, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def batches(self, request, pk=None):
        """获取产品批次信息"""
        product = self.get_object()
        batches = Batch.objects.filter(product=product)
        
        # 添加批次库存数量统计
        batches = batches.annotate(
            total_quantity=Sum('batch_inventory__quantity', default=0),
            available_quantity=Sum(
                F('batch_inventory__quantity') - F('batch_inventory__reserved_quantity'),
                default=0
            )
        )
        
        serializer = BatchSerializer(batches, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def serial_numbers(self, request, pk=None):
        """获取产品序列号信息"""
        product = self.get_object()
        serial_numbers = SerialNumber.objects.filter(product=product)
        
        # 过滤条件
        status_param = request.query_params.get('status')
        batch = request.query_params.get('batch')
        
        if status_param is not None:
            serial_numbers = serial_numbers.filter(status=status_param)
        if batch is not None:
            serial_numbers = serial_numbers.filter(batch=batch)
        
        serializer = SerialNumberSerializer(serial_numbers, many=True)
        return Response(serializer.data)

class BatchViewSet(viewsets.ModelViewSet):
    """批次视图集"""
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['batch_number', 'supplier']
    ordering_fields = ['batch_number', 'expiry_date', 'received_date', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 添加批次库存数量统计
        queryset = queryset.annotate(
            total_quantity=Sum('batch_inventory__quantity', default=0),
            available_quantity=Sum(
                F('batch_inventory__quantity') - F('batch_inventory__reserved_quantity'),
                default=0
            )
        )
        
        # 过滤条件
        product = self.request.query_params.get('product')
        expiring_soon = self.request.query_params.get('expiring_soon')
        expired = self.request.query_params.get('expired')
        
        if product is not None:
            queryset = queryset.filter(product=product)
        if expiring_soon is not None and expiring_soon.lower() == 'true':
            # 30天内过期
            thirty_days_later = timezone.now().date() + timezone.timedelta(days=30)
            queryset = queryset.filter(
                expiry_date__isnull=False,
                expiry_date__lte=thirty_days_later,
                expiry_date__gt=timezone.now().date()
            )
        if expired is not None and expired.lower() == 'true':
            queryset = queryset.filter(
                expiry_date__isnull=False,
                expiry_date__lt=timezone.now().date()
            )
        
        return queryset

    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """获取批次库存信息"""
        batch = self.get_object()
        batch_inventory = BatchInventory.objects.filter(batch=batch)
        
        # 添加可用数量计算
        batch_inventory = batch_inventory.annotate(
            available_quantity=F('quantity') - F('reserved_quantity')
        )
        
        serializer = BatchInventorySerializer(batch_inventory, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def serial_numbers(self, request, pk=None):
        """获取批次序列号信息"""
        batch = self.get_object()
        serial_numbers = SerialNumber.objects.filter(batch=batch)
        
        # 过滤条件
        status_param = request.query_params.get('status')
        
        if status_param is not None:
            serial_numbers = serial_numbers.filter(status=status_param)
        
        serializer = SerialNumberSerializer(serial_numbers, many=True)
        return Response(serializer.data)

class SerialNumberViewSet(viewsets.ModelViewSet):
    """序列号视图集"""
    queryset = SerialNumber.objects.all()
    serializer_class = SerialNumberSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['serial_number']
    ordering_fields = ['serial_number', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤条件
        product = self.request.query_params.get('product')
        batch = self.request.query_params.get('batch')
        status_param = self.request.query_params.get('status')
        location = self.request.query_params.get('location')
        
        if product is not None:
            queryset = queryset.filter(product=product)
        if batch is not None:
            queryset = queryset.filter(batch=batch)
        if status_param is not None:
            queryset = queryset.filter(status=status_param)
        if location is not None:
            queryset = queryset.filter(location=location)
        
        return queryset

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """更新序列号状态"""
        serial_number = self.get_object()
        status_param = request.data.get('status')
        location_id = request.data.get('location')
        notes = request.data.get('notes')
        
        if not status_param:
            return Response({'error': '状态不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        if status_param not in dict(SerialNumber.status.field.choices).keys():
            return Response({'error': '无效的状态值'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新状态
        serial_number.status = status_param
        
        # 更新位置
        if location_id:
            try:
                location = Location.objects.get(pk=location_id)
                serial_number.location = location
            except Location.DoesNotExist:
                return Response({'error': '位置不存在'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新备注
        if notes:
            serial_number.notes = notes
        
        serial_number.save()
        serializer = self.get_serializer(serial_number)
        return Response(serializer.data)

class InventoryViewSet(viewsets.ModelViewSet):
    """库存视图集"""
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['product__name', 'product__sku', 'location__name', 'location__code']
    ordering_fields = ['product__name', 'location__name', 'quantity', 'created_at']
    ordering = ['product__name', 'location__name']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 添加可用数量计算
        queryset = queryset.annotate(
            available_quantity=F('quantity') - F('reserved_quantity')
        )
        
        # 过滤条件
        product = self.request.query_params.get('product')
        location = self.request.query_params.get('location')
        warehouse = self.request.query_params.get('warehouse')
        low_stock = self.request.query_params.get('low_stock')
        out_of_stock = self.request.query_params.get('out_of_stock')
        
        if product is not None:
            queryset = queryset.filter(product=product)
        if location is not None:
            queryset = queryset.filter(location=location)
        if warehouse is not None:
            queryset = queryset.filter(location__warehouse=warehouse)
        if low_stock is not None and low_stock.lower() == 'true':
            queryset = queryset.filter(
                quantity__gt=0,
                quantity__lte=F('product__min_stock_level')
            )
        if out_of_stock is not None and out_of_stock.lower() == 'true':
            queryset = queryset.filter(quantity__lte=0)
        
        return queryset

    @action(detail=True, methods=['get'])
    def batch_inventory(self, request, pk=None):
        """获取库存批次信息"""
        inventory = self.get_object()
        batch_inventory = BatchInventory.objects.filter(inventory=inventory)
        
        # 添加可用数量计算
        batch_inventory = batch_inventory.annotate(
            available_quantity=F('quantity') - F('reserved_quantity')
        )
        
        serializer = BatchInventorySerializer(batch_inventory, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """获取库存交易记录"""
        inventory = self.get_object()
        transactions = InventoryTransaction.objects.filter(inventory=inventory)
        
        # 过滤条件
        transaction_type = request.query_params.get('transaction_type')
        reference_type = request.query_params.get('reference_type')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if transaction_type is not None:
            transactions = transactions.filter(transaction_type=transaction_type)
        if reference_type is not None:
            transactions = transactions.filter(reference_type=reference_type)
        if start_date is not None:
            transactions = transactions.filter(created_at__gte=start_date)
        if end_date is not None:
            transactions = transactions.filter(created_at__lte=end_date)
        
        serializer = InventoryTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def adjust(self, request, pk=None):
        """调整库存数量"""
        inventory = self.get_object()
        quantity = request.data.get('quantity')
        batch_id = request.data.get('batch')
        reason = request.data.get('reason')
        notes = request.data.get('notes')
        
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response({'error': '数量必须是整数'}, status=status.HTTP_400_BAD_REQUEST)
        
        if quantity == 0:
            return Response({'error': '调整数量不能为0'}, status=status.HTTP_400_BAD_REQUEST)
        
        batch = None
        if batch_id:
            try:
                batch = Batch.objects.get(pk=batch_id, product=inventory.product)
            except Batch.DoesNotExist:
                return Response({'error': '批次不存在或不属于该产品'}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # 记录之前的数量
            previous_quantity = inventory.quantity
            
            # 更新库存数量
            if quantity > 0:
                inventory.quantity += quantity
                transaction_type = 'increase'
            else:
                # 确保不会减到负数
                if inventory.quantity + quantity < 0:
                    return Response({'error': '库存不足，无法减少'}, status=status.HTTP_400_BAD_REQUEST)
                inventory.quantity += quantity
                transaction_type = 'decrease'
            
            inventory.save()
            
            # 更新批次库存
            if batch:
                batch_inventory, created = BatchInventory.objects.get_or_create(
                    inventory=inventory,
                    batch=batch,
                    defaults={'quantity': 0, 'reserved_quantity': 0}
                )
                
                previous_batch_quantity = batch_inventory.quantity
                
                if quantity > 0:
                    batch_inventory.quantity += quantity
                else:
                    # 确保不会减到负数
                    if batch_inventory.quantity + quantity < 0:
                        # 回滚库存更新
                        inventory.quantity = previous_quantity
                        inventory.save()
                        return Response({'error': '批次库存不足，无法减少'}, status=status.HTTP_400_BAD_REQUEST)
                    batch_inventory.quantity += quantity
                
                batch_inventory.save()
            
            # 创建库存交易记录
            transaction_record = InventoryTransaction.objects.create(
                inventory=inventory,
                batch=batch,
                transaction_type=transaction_type,
                quantity=abs(quantity),
                previous_quantity=previous_quantity,
                new_quantity=inventory.quantity,
                reference_type='adjustment',
                reference_id=None,
                notes=f"原因: {reason or '未指定'}\n备注: {notes or '无'}",
                user=request.user
            )
            
            # 检查是否需要创建库存警报
            self._check_inventory_alerts(inventory)
        
        serializer = self.get_serializer(inventory)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def move(self, request):
        """移动库存"""
        product_id = request.data.get('product')
        source_location_id = request.data.get('source_location')
        destination_location_id = request.data.get('destination_location')
        quantity = request.data.get('quantity')
        batch_id = request.data.get('batch')
        notes = request.data.get('notes')
        
        # 验证参数
        if not all([product_id, source_location_id, destination_location_id, quantity]):
            return Response({'error': '产品、源位置、目标位置和数量不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response({'error': '数量必须大于0'}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError):
            return Response({'error': '数量必须是正整数'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.get(pk=product_id)
            source_location = Location.objects.get(pk=source_location_id)
            destination_location = Location.objects.get(pk=destination_location_id)
        except (Product.DoesNotExist, Location.DoesNotExist):
            return Response({'error': '产品或位置不存在'}, status=status.HTTP_400_BAD_REQUEST)
        
        if source_location == destination_location:
            return Response({'error': '源位置和目标位置不能相同'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取源库存
        try:
            source_inventory = Inventory.objects.get(product=product, location=source_location)
        except Inventory.DoesNotExist:
            return Response({'error': '源位置没有该产品的库存'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查源库存是否足够
        if source_inventory.quantity - source_inventory.reserved_quantity < quantity:
            return Response({'error': '源位置可用库存不足'}, status=status.HTTP_400_BAD_REQUEST)
        
        batch = None
        if batch_id:
            try:
                batch = Batch.objects.get(pk=batch_id, product=product)
                # 检查批次库存是否足够
                try:
                    source_batch_inventory = BatchInventory.objects.get(inventory=source_inventory, batch=batch)
                    if source_batch_inventory.quantity - source_batch_inventory.reserved_quantity < quantity:
                        return Response({'error': '源位置该批次的可用库存不足'}, status=status.HTTP_400_BAD_REQUEST)
                except BatchInventory.DoesNotExist:
                    return Response({'error': '源位置没有该批次的库存'}, status=status.HTTP_400_BAD_REQUEST)
            except Batch.DoesNotExist:
                return Response({'error': '批次不存在或不属于该产品'}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # 获取或创建目标库存
            destination_inventory, created = Inventory.objects.get_or_create(
                product=product,
                location=destination_location,
                defaults={'quantity': 0, 'reserved_quantity': 0}
            )
            
            # 记录之前的数量
            source_previous_quantity = source_inventory.quantity
            destination_previous_quantity = destination_inventory.quantity
            
            # 更新源库存和目标库存
            source_inventory.quantity -= quantity
            destination_inventory.quantity += quantity
            
            source_inventory.save()
            destination_inventory.save()
            
            # 更新批次库存
            if batch:
                source_batch_inventory = BatchInventory.objects.get(inventory=source_inventory, batch=batch)
                source_batch_previous_quantity = source_batch_inventory.quantity
                
                destination_batch_inventory, created = BatchInventory.objects.get_or_create(
                    inventory=destination_inventory,
                    batch=batch,
                    defaults={'quantity': 0, 'reserved_quantity': 0}
                )
                destination_batch_previous_quantity = destination_batch_inventory.quantity
                
                source_batch_inventory.quantity -= quantity
                destination_batch_inventory.quantity += quantity
                
                source_batch_inventory.save()
                destination_batch_inventory.save()
            
            # 创建库存交易记录 - 源位置
            source_transaction = InventoryTransaction.objects.create(
                inventory=source_inventory,
                batch=batch,
                transaction_type='decrease',
                quantity=quantity,
                previous_quantity=source_previous_quantity,
                new_quantity=source_inventory.quantity,
                reference_type='movement_out',
                reference_id=str(destination_location.id),
                notes=f"移动到: {destination_location.name}\n备注: {notes or '无'}",
                user=request.user
            )
            
            # 创建库存交易记录 - 目标位置
            destination_transaction = InventoryTransaction.objects.create(
                inventory=destination_inventory,
                batch=batch,
                transaction_type='increase',
                quantity=quantity,
                previous_quantity=destination_previous_quantity,
                new_quantity=destination_inventory.quantity,
                reference_type='movement_in',
                reference_id=str(source_location.id),
                notes=f"移动自: {source_location.name}\n备注: {notes or '无'}",
                user=request.user
            )
            
            # 检查是否需要创建库存警报
            self._check_inventory_alerts(source_inventory)
            self._check_inventory_alerts(destination_inventory)
        
        return Response({
            'source': InventorySerializer(source_inventory).data,
            'destination': InventorySerializer(destination_inventory).data
        })

    def _check_inventory_alerts(self, inventory):
        """检查并创建库存警报"""
        product = inventory.product
        total_quantity = Inventory.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0
        
        # 检查低库存警报
        if 0 < total_quantity <= product.min_stock_level:
            InventoryAlert.objects.get_or_create(
                product=product,
                alert_type='low_stock',
                status='active',
                defaults={
                    'message': f"产品 {product.name} ({product.sku}) 库存低于最低库存水平。当前库存: {total_quantity}, 最低库存水平: {product.min_stock_level}"
                }
            )
        # 检查缺货警报
        elif total_quantity <= 0:
            InventoryAlert.objects.get_or_create(
                product=product,
                alert_type='out_of_stock',
                status='active',
                defaults={
                    'message': f"产品 {product.name} ({product.sku}) 已缺货。"
                }
            )
        # 如果库存恢复正常，将相关警报标记为已解决
        else:
            InventoryAlert.objects.filter(
                product=product,
                alert_type__in=['low_stock', 'out_of_stock'],
                status='active'
            ).update(status='resolved')
        
        # 检查批次过期警报
        thirty_days_later = timezone.now().date() + timezone.timedelta(days=30)
        expiring_batches = Batch.objects.filter(
            product=product,
            expiry_date__isnull=False,
            expiry_date__lte=thirty_days_later,
            expiry_date__gt=timezone.now().date()
        )
        
        for batch in expiring_batches:
            batch_quantity = BatchInventory.objects.filter(batch=batch).aggregate(total=Sum('quantity'))['total'] or 0
            if batch_quantity > 0:
                days_until_expiry = (batch.expiry_date - timezone.now().date()).days
                InventoryAlert.objects.get_or_create(
                    product=product,
                    alert_type='expiring',
                    status='active',
                    defaults={
                        'message': f"产品 {product.name} ({product.sku}) 批次 {batch.batch_number} 将在 {days_until_expiry} 天后过期。当前库存: {batch_quantity}"
                    }
                )
        
        # 检查已过期批次警报
        expired_batches = Batch.objects.filter(
            product=product,
            expiry_date__isnull=False,
            expiry_date__lt=timezone.now().date()
        )
        
        for batch in expired_batches:
            batch_quantity = BatchInventory.objects.filter(batch=batch).aggregate(total=Sum('quantity'))['total'] or 0
            if batch_quantity > 0:
                days_since_expiry = (timezone.now().date() - batch.expiry_date).days
                InventoryAlert.objects.get_or_create(
                    product=product,
                    alert_type='expired',
                    status='active',
                    defaults={
                        'message': f"产品 {product.name} ({product.sku}) 批次 {batch.batch_number} 已过期 {days_since_expiry} 天。当前库存: {batch_quantity}"
                    }
                )

class InventoryCountViewSet(viewsets.ModelViewSet):
    """库存盘点视图集"""
    queryset = InventoryCount.objects.all()
    serializer_class = InventoryCountSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['location__name', 'notes']
    ordering_fields = ['created_at', 'started_at', 'completed_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 添加统计信息
        queryset = queryset.annotate(
            items_count=Count('items'),
            completed_items_count=Count('items', filter=Q(items__counted_quantity__isnull=False)),
            discrepancy_items_count=Count('items', filter=Q(items__is_discrepancy=True))
        )
        
        # 过滤条件
        location = self.request.query_params.get('location')
        status_param = self.request.query_params.get('status')
        count_type = self.request.query_params.get('count_type')
        assigned_to = self.request.query_params.get('assigned_to')
        created_by = self.request.query_params.get('created_by')
        
        if location is not None:
            queryset = queryset.filter(location=location)
        if status_param is not None:
            queryset = queryset.filter(status=status_param)
        if count_type is not None:
            queryset = queryset.filter(count_type=count_type)
        if assigned_to is not None:
            queryset = queryset.filter(assigned_to=assigned_to)
        if created_by is not None:
            queryset = queryset.filter(created_by=created_by)
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return InventoryCountDetailSerializer
        return InventoryCountSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """开始盘点"""
        inventory_count = self.get_object()
        
        if inventory_count.status != 'pending':
            return Response({'error': '只有待处理的盘点才能开始'}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # 更新盘点状态
            inventory_count.status = 'in_progress'
            inventory_count.started_at = timezone.now()
            inventory_count.save()
            
            # 如果还没有盘点项目，自动创建
            if not inventory_count.items.exists():
                # 获取位置的所有库存
                inventories = Inventory.objects.filter(location=inventory_count.location)
                
                # 创建盘点项目
                for inventory in inventories:
                    InventoryCountItem.objects.create(
                        inventory_count=inventory_count,
                        inventory=inventory,
                        expected_quantity=inventory.quantity
                    )
        
        serializer = self.get_serializer(inventory_count)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """完成盘点"""
        inventory_count = self.get_object()
        
        if inventory_count.status != 'in_progress':
            return Response({'error': '只有进行中的盘点才能完成'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查是否所有项目都已盘点
        uncounted_items = inventory_count.items.filter(counted_quantity__isnull=True)
        if uncounted_items.exists():
            return Response({'error': '还有未盘点的项目'}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # 更新盘点状态
            inventory_count.status = 'completed'
            inventory_count.completed_at = timezone.now()
            inventory_count.save()
            
            # 处理盘点差异
            for item in inventory_count.items.filter(is_discrepancy=True):
                inventory = item.inventory
                difference = item.counted_quantity - item.expected_quantity
                
                if difference != 0:
                    # 调整库存
                    previous_quantity = inventory.quantity
                    inventory.quantity = item.counted_quantity
                    inventory.save()
                    
                    # 创建库存交易记录
                    transaction_type = 'increase' if difference > 0 else 'decrease'
                    InventoryTransaction.objects.create(
                        inventory=inventory,
                        transaction_type=transaction_type,
                        quantity=abs(difference),
                        previous_quantity=previous_quantity,
                        new_quantity=inventory.quantity,
                        reference_type='inventory_count',
                        reference_id=str(inventory_count.id),
                        notes=f"盘点调整: {inventory_count.id}\n差异: {difference}",
                        user=request.user
                    )
                    
                    # 检查是否需要创建库存警报
                    self._check_inventory_alerts(inventory)
        
        serializer = self.get_serializer(inventory_count)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消盘点"""
        inventory_count = self.get_object()
        
        if inventory_count.status not in ['pending', 'in_progress']:
            return Response({'error': '只有待处理或进行中的盘点才能取消'}, status=status.HTTP_400_BAD_REQUEST)
        
        inventory_count.status = 'cancelled'
        inventory_count.save()
        
        serializer = self.get_serializer(inventory_count)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """分配盘点任务"""
        inventory_count = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': '用户ID不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)
        
        inventory_count.assigned_to = user
        inventory_count.save()
        
        serializer = self.get_serializer(inventory_count)
        return Response(serializer.data)

    def _check_inventory_alerts(self, inventory):
        """检查并创建库存警报"""
        product = inventory.product
        total_quantity = Inventory.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0
        
        # 检查低库存警报
        if 0 < total_quantity <= product.min_stock_level:
            InventoryAlert.objects.get_or_create(
                product=product,
                alert_type='low_stock',
                status='active',
                defaults={
                    'message': f"产品 {product.name} ({product.sku}) 库存低于最低库存水平。当前库存: {total_quantity}, 最低库存水平: {product.min_stock_level}"
                }
            )
        # 检查缺货警报
        elif total_quantity <= 0:
            InventoryAlert.objects.get_or_create(
                product=product,
                alert_type='out_of_stock',
                status='active',
                defaults={
                    'message': f"产品 {product.name} ({product.sku}) 已缺货。"
                }
            )
        # 如果库存恢复正常，将相关警报标记为已解决
        else:
            InventoryAlert.objects.filter(
                product=product,
                alert_type__in=['low_stock', 'out_of_stock'],
                status='active'
            ).update(status='resolved')

class InventoryCountItemViewSet(viewsets.ModelViewSet):
    """库存盘点项目视图集"""
    queryset = InventoryCountItem.objects.all()
    serializer_class = InventoryCountItemSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['inventory__product__name', 'inventory__product__sku', 'notes']
    ordering_fields = ['inventory__product__name', 'expected_quantity', 'counted_quantity', 'is_discrepancy']
    ordering = ['inventory__product__name']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤条件
        inventory_count = self.request.query_params.get('inventory_count')
        is_discrepancy = self.request.query_params.get('is_discrepancy')
        is_counted = self.request.query_params.get('is_counted')
        
        if inventory_count is not None:
            queryset = queryset.filter(inventory_count=inventory_count)
        if is_discrepancy is not None:
            queryset = queryset.filter(is_discrepancy=is_discrepancy == 'true')
        if is_counted is not None:
            if is_counted == 'true':
                queryset = queryset.filter(counted_quantity__isnull=False)
            else:
                queryset = queryset.filter(counted_quantity__isnull=True)
        
        return queryset

    @action(detail=True, methods=['post'])
    def count(self, request, pk=None):
        """记录盘点数量"""
        count_item = self.get_object()
        counted_quantity = request.data.get('counted_quantity')
        notes = request.data.get('notes')
        
        if count_item.inventory_count.status != 'in_progress':
            return Response({'error': '只有进行中的盘点才能记录数量'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            counted_quantity = int(counted_quantity)
            if counted_quantity < 0:
                return Response({'error': '盘点数量不能为负数'}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError):
            return Response({'error': '盘点数量必须是非负整数'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新盘点项目
        count_item.counted_quantity = counted_quantity
        count_item.is_discrepancy = counted_quantity != count_item.expected_quantity
        if notes:
            count_item.notes = notes
        count_item.save()
        
        serializer = self.get_serializer(count_item)
        return Response(serializer.data)

class InventoryAlertViewSet(viewsets.ModelViewSet):
    """库存警报视图集"""
    queryset = InventoryAlert.objects.all()
    serializer_class = InventoryAlertSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['product__name', 'product__sku', 'message']
    ordering_fields = ['created_at', 'alert_type', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤条件
        product = self.request.query_params.get('product')
        alert_type = self.request.query_params.get('alert_type')
        status_param = self.request.query_params.get('status')
        
        if product is not None:
            queryset = queryset.filter(product=product)
        if alert_type is not None:
            queryset = queryset.filter(alert_type=alert_type)
        if status_param is not None:
            queryset = queryset.filter(status=status_param)
        
        return queryset

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """确认警报"""
        alert = self.get_object()
        
        if alert.status != 'active':
            return Response({'error': '只有激活状态的警报才能确认'}, status=status.HTTP_400_BAD_REQUEST)
        
        alert.status = 'acknowledged'
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """解决警报"""
        alert = self.get_object()
        
        if alert.status == 'resolved':
            return Response({'error': '警报已经解决'}, status=status.HTTP_400_BAD_REQUEST)
        
        alert.status = 'resolved'
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
