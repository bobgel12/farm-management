from rest_framework import serializers
from .models import House, HouseMonitoringSnapshot, HouseAlarm, Device, DeviceStatus, ControlSettings, TemperatureCurve, HouseConfiguration, Sensor
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


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for devices"""
    
    class Meta:
        model = Device
        fields = [
            'id', 'house', 'device_type', 'device_number', 'name',
            'status', 'percentage', 'last_update', 'last_checked', 'notes'
        ]
        read_only_fields = ['id', 'last_update']


class DeviceStatusSerializer(serializers.ModelSerializer):
    """Serializer for device status history"""
    
    class Meta:
        model = DeviceStatus
        fields = ['id', 'device', 'status', 'percentage', 'timestamp', 'notes']
        read_only_fields = ['id', 'timestamp']


class TemperatureCurveSerializer(serializers.ModelSerializer):
    """Serializer for temperature curve points"""
    
    class Meta:
        model = TemperatureCurve
        fields = ['id', 'day', 'target_temperature', 'notes']
        read_only_fields = ['id']


class ControlSettingsSerializer(serializers.ModelSerializer):
    """Serializer for house control settings"""
    temperature_curves = TemperatureCurveSerializer(many=True, read_only=True)
    
    class Meta:
        model = ControlSettings
        fields = [
            'id', 'house', 'temperature_curve', 'min_temperature', 'max_temperature',
            'target_temperature', 'temperature_offset', 'humidity_target',
            'humidity_treatment_enabled', 'humidity_min', 'humidity_max',
            'co2_target', 'co2_treatment_enabled', 'co2_max',
            'ventilation_mode', 'static_pressure_target', 'static_pressure_min',
            'static_pressure_max', 'lighting_schedule', 'light_dimmer_level',
            'cooling_pad_enabled', 'cooling_pad_threshold',
            'fogger_enabled', 'fogger_threshold',
            'water_on_demand_enabled', 'feed_schedule',
            'temperature_curves', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SensorSerializer(serializers.ModelSerializer):
    """Serializer for sensors"""
    
    class Meta:
        model = Sensor
        fields = [
            'id', 'house', 'sensor_type', 'sensor_number', 'location',
            'calibration_data', 'last_calibration', 'calibration_due_date',
            'is_active', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class HouseConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for house configuration"""
    sensors = SensorSerializer(many=True, read_only=True)
    
    class Meta:
        model = HouseConfiguration
        fields = [
            'id', 'house', 'length_feet', 'width_feet', 'height_feet',
            'total_square_feet', 'sensor_layout', 'relay_layout',
            'fan_air_capacity_cfm', 'tunnel_fan_count', 'exhaust_fan_count',
            'stir_fan_count', 'scale_settings', 'silo_count', 'auger_count',
            'feeder_count', 'drinker_count', 'sensors', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_square_feet', 'created_at', 'updated_at']


class HouseComparisonSerializer(serializers.Serializer):
    """Serializer for house comparison data"""
    house_id = serializers.IntegerField()
    house_number = serializers.IntegerField()
    farm_id = serializers.IntegerField()
    farm_name = serializers.CharField()
    
    # House Status
    current_day = serializers.IntegerField(allow_null=True)
    status = serializers.CharField()
    is_full_house = serializers.BooleanField()
    
    # Time
    last_update_time = serializers.DateTimeField(allow_null=True)
    
    # Metrics
    average_temperature = serializers.FloatField(allow_null=True)
    static_pressure = serializers.FloatField(allow_null=True)
    inside_humidity = serializers.FloatField(allow_null=True)
    tunnel_temperature = serializers.FloatField(allow_null=True)
    outside_temperature = serializers.FloatField(allow_null=True)
    ventilation_mode = serializers.CharField(allow_null=True)
    
    # Additional status
    is_connected = serializers.BooleanField()
    has_alarms = serializers.BooleanField()
    alarm_status = serializers.CharField()
