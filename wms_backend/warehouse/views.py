from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from warehouse.models import Warehouse, Zone, Location, Task, TaskHistory
from warehouse.serializers import WarehouseSerializer, ZoneSerializer, LocationSerializer, TaskSerializer, TaskHistorySerializer
from core.middleware import get_current_tenant
from django.utils import timezone

class WarehouseViewSet(viewsets.ModelViewSet):
    """
    仓库管理视图集
    """
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    
    def get_queryset(self):
        tenant = get_current_tenant()
        return Warehouse.objects.filter(tenant=tenant)
    
    def perform_create(self, serializer):
        tenant = get_current_tenant()
        serializer.save(tenant=tenant)

class ZoneViewSet(viewsets.ModelViewSet):
    """
    区域管理视图集
    """
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
    
    def get_queryset(self):
        tenant = get_current_tenant()
        warehouse_id = self.request.query_params.get('warehouse_id')
        queryset = Zone.objects.filter(warehouse__tenant=tenant)
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        return queryset

class LocationViewSet(viewsets.ModelViewSet):
    """
    位置管理视图集
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    
    def get_queryset(self):
        tenant = get_current_tenant()
        warehouse_id = self.request.query_params.get('warehouse_id')
        zone_id = self.request.query_params.get('zone_id')
        queryset = Location.objects.filter(warehouse__tenant=tenant)
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        if zone_id:
            queryset = queryset.filter(zone_id=zone_id)
        return queryset

class TaskViewSet(viewsets.ModelViewSet):
    """
    任务管理视图集
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    def get_queryset(self):
        tenant = get_current_tenant()
        status = self.request.query_params.get('status')
        task_type = self.request.query_params.get('task_type')
        warehouse_id = self.request.query_params.get('warehouse_id')
        assigned_to_me = self.request.query_params.get('assigned_to_me')
        
        queryset = Task.objects.filter(tenant=tenant)
        
        if status:
            queryset = queryset.filter(status=status)
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        if assigned_to_me and assigned_to_me.lower() == 'true':
            queryset = queryset.filter(assigned_user=self.request.user)
            
        return queryset
    
    def perform_create(self, serializer):
        tenant = get_current_tenant()
        serializer.save(tenant=tenant)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """
        分配任务给用户
        """
        task = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': '请提供用户ID'}, status=status.HTTP_400_BAD_REQUEST)
        
        task.assigned_user_id = user_id
        task.status = 'assigned'
        task.save()
        
        # 创建任务历史记录
        TaskHistory.objects.create(
            task=task,
            status='assigned',
            user=request.user,
            notes=f'任务已分配给用户ID: {user_id}'
        )
        
        return Response({'status': '任务已分配'})
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        开始任务
        """
        task = self.get_object()
        
        if task.status != 'assigned':
            return Response({'error': '只有已分配的任务才能开始'}, status=status.HTTP_400_BAD_REQUEST)
        
        if task.assigned_user_id != request.user.id:
            return Response({'error': '只有被分配的用户才能开始任务'}, status=status.HTTP_403_FORBIDDEN)
        
        task.status = 'in_progress'
        task.start_time = timezone.now()
        task.save()
        
        # 创建任务历史记录
        TaskHistory.objects.create(
            task=task,
            status='in_progress',
            user=request.user,
            notes='任务已开始'
        )
        
        return Response({'status': '任务已开始'})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        完成任务
        """
        task = self.get_object()
        
        if task.status != 'in_progress':
            return Response({'error': '只有进行中的任务才能完成'}, status=status.HTTP_400_BAD_REQUEST)
        
        if task.assigned_user_id != request.user.id:
            return Response({'error': '只有被分配的用户才能完成任务'}, status=status.HTTP_403_FORBIDDEN)
        
        task.status = 'completed'
        task.end_time = timezone.now()
        task.save()
        
        # 创建任务历史记录
        TaskHistory.objects.create(
            task=task,
            status='completed',
            user=request.user,
            notes='任务已完成'
        )
        
        return Response({'status': '任务已完成'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        取消任务
        """
        task = self.get_object()
        
        if task.status in ['completed', 'cancelled']:
            return Response({'error': '已完成或已取消的任务不能取消'}, status=status.HTTP_400_BAD_REQUEST)
        
        task.status = 'cancelled'
        task.save()
        
        # 创建任务历史记录
        TaskHistory.objects.create(
            task=task,
            status='cancelled',
            user=request.user,
            notes=request.data.get('notes', '任务已取消')
        )
        
        return Response({'status': '任务已取消'})

class TaskHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    任务历史视图集（只读）
    """
    queryset = TaskHistory.objects.all()
    serializer_class = TaskHistorySerializer
    
    def get_queryset(self):
        task_id = self.kwargs.get('task_pk')
        return TaskHistory.objects.filter(task_id=task_id).order_by('-created_at')
