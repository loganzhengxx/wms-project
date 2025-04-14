from rest_framework import serializers
from .models import (
    Product, ProductCategory, ProductAttribute, ProductAttributeValue, 
    ProductImage, Batch, SerialNumber, Inventory, BatchInventory,
    InventoryTransaction, InventoryCount, InventoryCountItem, InventoryAlert
)
from warehouse.serializers import LocationSerializer

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description', 'parent', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class ProductAttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    
    class Meta:
        model = ProductAttributeValue
        fields = ['id', 'attribute', 'attribute_name', 'value', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary', 'created_at']
        read_only_fields = ['created_at']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    attribute_values = ProductAttributeValueSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)
    available_quantity = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'barcode', 'description', 'category', 'category_name',
            'cost_price', 'selling_price', 'min_stock_level', 'reorder_point',
            'weight', 'length', 'width', 'height', 'handling_instructions', 
            'storage_requirements', 'is_active', 'created_at', 'updated_at',
            'attribute_values', 'images', 'total_quantity', 'available_quantity'
        ]
        read_only_fields = ['created_at', 'updated_at', 'total_quantity', 'available_quantity']

class ProductDetailSerializer(ProductSerializer):
    category = ProductCategorySerializer(read_only=True)
    batches = serializers.SerializerMethodField()
    inventory_by_location = serializers.SerializerMethodField()
    
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['batches', 'inventory_by_location']
    
    def get_batches(self, obj):
        batches = Batch.objects.filter(product=obj)
        return BatchSerializer(batches, many=True).data
    
    def get_inventory_by_location(self, obj):
        inventory = Inventory.objects.filter(product=obj)
        return InventorySerializer(inventory, many=True).data

class BatchSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)
    available_quantity = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Batch
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'batch_number',
            'manufacturing_date', 'expiry_date', 'received_date', 'supplier',
            'notes', 'created_at', 'updated_at', 'total_quantity', 'available_quantity'
        ]
        read_only_fields = ['created_at', 'updated_at', 'total_quantity', 'available_quantity']

class SerialNumberSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    
    class Meta:
        model = SerialNumber
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'batch', 'batch_number',
            'serial_number', 'status', 'location', 'location_name', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    location_code = serializers.CharField(source='location.code', read_only=True)
    available_quantity = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Inventory
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'location', 'location_name',
            'location_code', 'quantity', 'reserved_quantity', 'available_quantity',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'available_quantity']

class BatchInventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='inventory.product.name', read_only=True)
    product_sku = serializers.CharField(source='inventory.product.sku', read_only=True)
    location_name = serializers.CharField(source='inventory.location.name', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    available_quantity = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = BatchInventory
        fields = [
            'id', 'inventory', 'product_name', 'product_sku', 'location_name',
            'batch', 'batch_number', 'quantity', 'reserved_quantity', 'available_quantity',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'available_quantity']

class InventoryTransactionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='inventory.product.name', read_only=True)
    product_sku = serializers.CharField(source='inventory.product.sku', read_only=True)
    location_name = serializers.CharField(source='inventory.location.name', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = InventoryTransaction
        fields = [
            'id', 'inventory', 'product_name', 'product_sku', 'location_name',
            'batch', 'batch_number', 'transaction_type', 'quantity',
            'previous_quantity', 'new_quantity', 'reference_type', 'reference_id',
            'notes', 'user', 'user_name', 'created_at'
        ]
        read_only_fields = ['created_at', 'previous_quantity', 'new_quantity']

class InventoryCountItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='inventory.product.name', read_only=True)
    product_sku = serializers.CharField(source='inventory.product.sku', read_only=True)
    location_name = serializers.CharField(source='inventory.location.name', read_only=True)
    
    class Meta:
        model = InventoryCountItem
        fields = [
            'id', 'inventory_count', 'inventory', 'product_name', 'product_sku',
            'location_name', 'expected_quantity', 'counted_quantity', 'is_discrepancy',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_discrepancy']

class InventoryCountSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source='location.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    completed_items_count = serializers.IntegerField(read_only=True)
    discrepancy_items_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = InventoryCount
        fields = [
            'id', 'location', 'location_name', 'count_type', 'status',
            'started_at', 'completed_at', 'notes', 'created_by', 'created_by_name',
            'assigned_to', 'assigned_to_name', 'created_at', 'updated_at',
            'items_count', 'completed_items_count', 'discrepancy_items_count'
        ]
        read_only_fields = ['created_at', 'updated_at', 'items_count', 
                           'completed_items_count', 'discrepancy_items_count']

class InventoryCountDetailSerializer(InventoryCountSerializer):
    items = InventoryCountItemSerializer(many=True, read_only=True)
    
    class Meta(InventoryCountSerializer.Meta):
        fields = InventoryCountSerializer.Meta.fields + ['items']

class InventoryAlertSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.username', read_only=True)
    
    class Meta:
        model = InventoryAlert
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'alert_type',
            'status', 'message', 'acknowledged_by', 'acknowledged_by_name',
            'acknowledged_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
