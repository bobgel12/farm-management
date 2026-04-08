from rest_framework import serializers
from .models import (
    House,
    HouseMonitoringSnapshot,
    HouseAlarm,
    Device,
    DeviceStatus,
    ControlSettings,
    TemperatureCurve,
    HouseConfiguration,
    Sensor,
    WaterConsumptionAlert,
    WaterConsumptionForecast,
)
from farms.serializers import FarmListSerializer
from .services.monitoring_contract import normalized_snapshot_contract


class HouseSerializer(serializers.ModelSerializer):
    farm = FarmListSerializer(read_only=True)
    farm_id = serializers.IntegerField(write_only=True)
    current_day = serializers.ReadOnlyField()
    current_age_days = serializers.ReadOnlyField()
    age_days = serializers.ReadOnlyField()  # Unified age (prefers current_age_days, fallback to current_day)
    days_remaining = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()

    class Meta:
        model = House
        fields = [
            'id', 'farm', 'farm_id', 'house_number', 'chicken_in_date',
            'chicken_out_date', 'chicken_out_day', 'is_active',
            'current_day', 'current_age_days', 'age_days', 'days_remaining', 'status',
            'is_integrated', 'batch_start_date', 'expected_harvest_date',
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
    current_age_days = serializers.ReadOnlyField()
    age_days = serializers.ReadOnlyField()  # Unified age (prefers current_age_days, fallback to current_day)
    days_remaining = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()

    class Meta:
        model = House
        fields = [
            'id', 'farm_name', 'house_number', 'chicken_in_date',
            'chicken_out_date', 'current_day', 'current_age_days', 'age_days',
            'days_remaining', 'status', 'is_active', 'is_integrated',
            'batch_start_date', 'expected_harvest_date'
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
    source_timestamp = serializers.SerializerMethodField()
    
    class Meta:
        model = HouseMonitoringSnapshot
        fields = [
            'id', 'timestamp', 'average_temperature', 'outside_temperature',
            'humidity', 'static_pressure', 'target_temperature',
            'ventilation_level', 'growth_day', 'bird_count', 'livability',
            'water_consumption', 'feed_consumption', 'airflow_cfm',
            'airflow_percentage', 'connection_status', 'alarm_status',
            'has_alarms', 'is_connected', 'source_timestamp'
        ]
        read_only_fields = ['id', 'timestamp']

    def get_source_timestamp(self, obj):
        return normalized_snapshot_contract(obj).get('source_timestamp')


class HouseMonitoringSnapshotSerializer(serializers.ModelSerializer):
    """Full serializer for monitoring snapshots"""
    has_alarms = serializers.ReadOnlyField()
    is_connected = serializers.ReadOnlyField()
    house_number = serializers.IntegerField(source='house.house_number', read_only=True)
    farm_name = serializers.CharField(source='house.farm.name', read_only=True)
    alarms = HouseAlarmSerializer(many=True, read_only=True, source='alarms.filter(is_active=True)')
    normalized_contract = serializers.SerializerMethodField()
    
    class Meta:
        model = HouseMonitoringSnapshot
        fields = [
            'id', 'house', 'house_number', 'farm_name', 'timestamp',
            'average_temperature', 'outside_temperature', 'humidity',
            'static_pressure', 'target_temperature', 'ventilation_level',
            'growth_day', 'bird_count', 'livability', 'water_consumption',
            'feed_consumption', 'airflow_cfm', 'airflow_percentage',
            'connection_status', 'alarm_status', 'has_alarms', 'is_connected',
            'sensor_data', 'raw_data', 'alarms', 'normalized_contract'
        ]
        read_only_fields = ['id', 'timestamp', 'alarms']

    def get_normalized_contract(self, obj):
        return normalized_snapshot_contract(obj)


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
    age_days = serializers.IntegerField(allow_null=True)
    current_age_days = serializers.IntegerField(allow_null=True)
    is_integrated = serializers.BooleanField(default=False)
    status = serializers.CharField()
    is_full_house = serializers.BooleanField()
    
    # Time
    last_update_time = serializers.DateTimeField(allow_null=True)
    
    # Metrics - Temperature
    average_temperature = serializers.FloatField(allow_null=True)
    outside_temperature = serializers.FloatField(allow_null=True)
    tunnel_temperature = serializers.FloatField(allow_null=True)
    target_temperature = serializers.FloatField(allow_null=True)
    
    # Metrics - Environment
    static_pressure = serializers.FloatField(allow_null=True)
    inside_humidity = serializers.FloatField(allow_null=True)
    ventilation_mode = serializers.CharField(allow_null=True)
    ventilation_level = serializers.FloatField(allow_null=True)
    airflow_cfm = serializers.FloatField(allow_null=True)
    airflow_percentage = serializers.FloatField(allow_null=True)
    
    # Metrics - Consumption (Daily)
    water_consumption = serializers.FloatField(allow_null=True)
    feed_consumption = serializers.FloatField(allow_null=True)
    water_per_bird = serializers.FloatField(allow_null=True)
    feed_per_bird = serializers.FloatField(allow_null=True)
    water_feed_ratio = serializers.FloatField(allow_null=True)
    
    # Metrics - Bird Status
    bird_count = serializers.IntegerField(allow_null=True)
    livability = serializers.FloatField(allow_null=True)
    growth_day = serializers.IntegerField(allow_null=True)
    
    # Additional status
    is_connected = serializers.BooleanField()
    has_alarms = serializers.BooleanField()
    alarm_status = serializers.CharField()
    active_alarms_count = serializers.IntegerField(allow_null=True)
    data_freshness_minutes = serializers.IntegerField(allow_null=True)
    heater_on = serializers.BooleanField(default=False)
    fan_on = serializers.BooleanField(default=False)
    wind_speed = serializers.FloatField(allow_null=True)
    wind_direction = serializers.FloatField(allow_null=True)
    wind_chill_temperature = serializers.FloatField(allow_null=True)


class WaterConsumptionAlertSerializer(serializers.ModelSerializer):
    house_number = serializers.IntegerField(source='house.house_number', read_only=True)
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    acknowledged_by_username = serializers.CharField(source='acknowledged_by.username', read_only=True)
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True)

    class Meta:
        model = WaterConsumptionAlert
        fields = [
            'id', 'house', 'house_number', 'farm', 'farm_name', 'alert_date', 'growth_day',
            'current_consumption', 'baseline_consumption', 'expected_consumption', 'increase_percentage',
            'severity', 'anomaly_direction', 'anomaly_reason', 'message', 'detection_method',
            'is_acknowledged', 'acknowledged_at', 'acknowledged_by', 'acknowledged_by_username',
            'is_resolved', 'resolved_at', 'resolved_by', 'resolved_by_username',
            'snoozed_until', 'email_sent', 'email_sent_at', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'farm', 'house_number', 'farm_name', 'acknowledged_at', 'acknowledged_by',
            'acknowledged_by_username', 'resolved_at', 'resolved_by', 'resolved_by_username',
            'email_sent', 'email_sent_at', 'created_at', 'updated_at',
        ]


class WaterConsumptionForecastSerializer(serializers.ModelSerializer):
    house_number = serializers.IntegerField(source='house.house_number', read_only=True)
    farm_name = serializers.CharField(source='farm.name', read_only=True)

    class Meta:
        model = WaterConsumptionForecast
        fields = [
            'id', 'house', 'house_number', 'farm', 'farm_name',
            'forecast_date', 'horizon_hours', 'predicted_consumption', 'lower_bound',
            'upper_bound', 'confidence_score', 'model_version', 'features',
            'source_date', 'created_at',
        ]
        read_only_fields = ['id', 'farm', 'house_number', 'farm_name', 'created_at']
