from rest_framework import serializers
from .models import (
    Report, ReportSchedule, ReportExecution, 
    Dashboard, DashboardWidget, KPI, KPIValue
)
from accounts.serializers import UserSerializer

class ReportSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'name', 'description', 'report_type', 'config',
            'is_public', 'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ReportDetailSerializer(ReportSerializer):
    shared_with = UserSerializer(many=True, read_only=True)
    
    class Meta(ReportSerializer.Meta):
        fields = ReportSerializer.Meta.fields + ['shared_with']

class ReportScheduleSerializer(serializers.ModelSerializer):
    report_name = serializers.CharField(source='report.name', read_only=True)
    
    class Meta:
        model = ReportSchedule
        fields = [
            'id', 'report', 'report_name', 'name', 'frequency', 
            'day_of_week', 'day_of_month', 'time_of_day',
            'email_subject', 'email_body', 'is_active',
            'last_run', 'next_run', 'created_at', 'updated_at'
        ]
        read_only_fields = ['last_run', 'next_run', 'created_at', 'updated_at']

class ReportScheduleDetailSerializer(ReportScheduleSerializer):
    recipients = UserSerializer(many=True, read_only=True)
    
    class Meta(ReportScheduleSerializer.Meta):
        fields = ReportScheduleSerializer.Meta.fields + ['recipients']

class ReportExecutionSerializer(serializers.ModelSerializer):
    report_name = serializers.CharField(source='report.name', read_only=True)
    schedule_name = serializers.CharField(source='schedule.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ReportExecution
        fields = [
            'id', 'report', 'report_name', 'schedule', 'schedule_name',
            'status', 'parameters', 'error_message',
            'started_at', 'completed_at', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['started_at', 'completed_at', 'created_at']

class ReportExecutionDetailSerializer(ReportExecutionSerializer):
    result_data = serializers.JSONField(read_only=True)
    
    class Meta(ReportExecutionSerializer.Meta):
        fields = ReportExecutionSerializer.Meta.fields + ['result_data']

class DashboardWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardWidget
        fields = [
            'id', 'dashboard', 'title', 'widget_type', 'data_source',
            'config', 'position_x', 'position_y', 'width', 'height',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class DashboardSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Dashboard
        fields = [
            'id', 'name', 'description', 'layout',
            'is_public', 'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class DashboardDetailSerializer(DashboardSerializer):
    widgets = DashboardWidgetSerializer(many=True, read_only=True)
    shared_with = UserSerializer(many=True, read_only=True)
    
    class Meta(DashboardSerializer.Meta):
        fields = DashboardSerializer.Meta.fields + ['widgets', 'shared_with']

class KPISerializer(serializers.ModelSerializer):
    class Meta:
        model = KPI
        fields = [
            'id', 'name', 'description', 'category', 'calculation_method',
            'unit', 'target_value', 'min_value', 'max_value',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class KPIValueSerializer(serializers.ModelSerializer):
    kpi_name = serializers.CharField(source='kpi.name', read_only=True)
    kpi_unit = serializers.CharField(source='kpi.unit', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = KPIValue
        fields = [
            'id', 'kpi', 'kpi_name', 'kpi_unit', 'date', 'value',
            'warehouse', 'warehouse_name', 'user', 'user_name', 'created_at'
        ]
        read_only_fields = ['created_at']
