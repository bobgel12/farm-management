from rest_framework import serializers
from .models import House, HouseMonitoringSnapshot, HouseAlarm
from farms.serializers import FarmListSerializer


class HouseSerializer(serializers.ModelSerializer):
    farm = FarmListSerializer(read_only=True)
    farm_id = serializers.IntegerField(write_only=True)
    current_day = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()

    class Meta:
        model = House
        fields = [
            'id', 'farm', 'farm_id', 'house_number', 'chicken_in_date',
            'chicken_out_date', 'chicken_out_day', 'is_active',
            'current_day', 'days_remaining', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        # Validate that chicken_out_day is positive
        if data.get('chicken_out_day', 40) <= 0:
            raise serializers.ValidationError("Chicken out day must be positive")
        
        # Validate that chicken_in_date is not in the future
        if data.get('chicken_in_date'):
            from django.utils import timezone
            if data['chicken_in_date'] > timezone.now().date():
                raise serializers.ValidationError("Chicken in date cannot be in the future")
        
        return data


class HouseListSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    current_day = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()

    class Meta:
        model = House
        fields = [
            'id', 'farm_name', 'house_number', 'chicken_in_date',
            'chicken_out_date', 'current_day', 'days_remaining',
            'status', 'is_active'
        ]


class HouseAlarmSerializer(serializers.ModelSerializer):
    """Serializer for house alarms"""
    
    class Meta:
        model = HouseAlarm
        fields = [
            'id', 'alarm_type', 'severity', 'message',
            'parameter_name', 'parameter_value', 'threshold_value',
            'is_active', 'is_resolved', 'resolved_at', 'resolved_by',
            'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class HouseMonitoringSummarySerializer(serializers.ModelSerializer):
    """Lightweight summary serializer for monitoring snapshots"""
    has_alarms = serializers.ReadOnlyField()
    is_connected = serializers.ReadOnlyField()
    
    class Meta:
        model = HouseMonitoringSnapshot
        fields = [
            'id', 'timestamp', 'average_temperature', 'outside_temperature',
            'humidity', 'static_pressure', 'target_temperature',
            'ventilation_level', 'growth_day', 'bird_count', 'livability',
            'water_consumption', 'feed_consumption', 'airflow_cfm',
            'airflow_percentage', 'connection_status', 'alarm_status',
            'has_alarms', 'is_connected'
        ]
        read_only_fields = ['id', 'timestamp']


class HouseMonitoringSnapshotSerializer(serializers.ModelSerializer):
    """Full serializer for monitoring snapshots"""
    has_alarms = serializers.ReadOnlyField()
    is_connected = serializers.ReadOnlyField()
    house_number = serializers.IntegerField(source='house.house_number', read_only=True)
    farm_name = serializers.CharField(source='house.farm.name', read_only=True)
    alarms = HouseAlarmSerializer(many=True, read_only=True, source='alarms.filter(is_active=True)')
    
    class Meta:
        model = HouseMonitoringSnapshot
        fields = [
            'id', 'house', 'house_number', 'farm_name', 'timestamp',
            'average_temperature', 'outside_temperature', 'humidity',
            'static_pressure', 'target_temperature', 'ventilation_level',
            'growth_day', 'bird_count', 'livability', 'water_consumption',
            'feed_consumption', 'airflow_cfm', 'airflow_percentage',
            'connection_status', 'alarm_status', 'has_alarms', 'is_connected',
            'sensor_data', 'raw_data', 'alarms'
        ]
        read_only_fields = ['id', 'timestamp', 'alarms']


class HouseMonitoringStatsSerializer(serializers.Serializer):
    """Serializer for statistical aggregations"""
    temperature = serializers.DictField()
    humidity = serializers.DictField()
    pressure = serializers.DictField()
    total_snapshots = serializers.IntegerField()
    period_days = serializers.IntegerField()
