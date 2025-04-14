from rest_framework import serializers
from warehouse.models import Warehouse, Zone, Location, Task, TaskHistory

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'tenant', 'name', 'code', 'address', 'contact_person', 
                 'phone', 'email', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ['id', 'warehouse', 'name', 'code', 'description', 
                 'zone_type', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class LocationSerializer(serializers.ModelSerializer):
    zone_name = serializers.ReadOnlyField(source='zone.name')
    warehouse_name = serializers.ReadOnlyField(source='warehouse.name')
    
    class Meta:
        model = Location
        fields = ['id', 'warehouse', 'warehouse_name', 'zone', 'zone_name', 
                 'name', 'code', 'barcode', 'location_type', 'aisle', 'rack', 
                 'shelf', 'bin', 'max_weight', 'max_volume', 'is_pickable', 
                 'is_receivable', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class TaskSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.ReadOnlyField(source='warehouse.name')
    assigned_user_name = serializers.ReadOnlyField(source='assigned_user.username')
    
    class Meta:
        model = Task
        fields = ['id', 'tenant', 'warehouse', 'warehouse_name', 'task_type', 
                 'reference_type', 'reference_id', 'priority', 'status', 
                 'assigned_user', 'assigned_user_name', 'start_time', 
                 'end_time', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class TaskHistorySerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = TaskHistory
        fields = ['id', 'task', 'status', 'user', 'user_name', 'notes', 'created_at']
        read_only_fields = ['created_at']
