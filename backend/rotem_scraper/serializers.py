from rest_framework import serializers
from .models import RotemDataPoint, MLPrediction, MLModel, RotemController, RotemFarm, RotemUser, RotemScrapeLog, RotemDailySummary
from farms.models import Farm


class RotemDataPointSerializer(serializers.ModelSerializer):
    controller_name = serializers.CharField(source='controller.controller_name', read_only=True)
    farm_name = serializers.CharField(source='controller.farm.name', read_only=True)
    
    class Meta:
        model = RotemDataPoint
        fields = ['id', 'controller', 'controller_name', 'farm_name', 'timestamp', 'data_type', 'value', 'unit', 'quality']


class MLPredictionSerializer(serializers.ModelSerializer):
    controller_name = serializers.CharField(source='controller.controller_name', read_only=True)
    farm_name = serializers.CharField(source='controller.farm.name', read_only=True)
    
    class Meta:
        model = MLPrediction
        fields = ['id', 'controller', 'controller_name', 'farm_name', 'prediction_type', 'predicted_at', 'confidence_score', 'prediction_data', 'is_active']


class RotemControllerSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    data_points_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RotemController
        fields = ['id', 'controller_id', 'controller_name', 'controller_type', 'is_connected', 'last_seen', 'farm', 'farm_name', 'data_points_count']
    
    def get_data_points_count(self, obj):
        return obj.data_points.count()


class IntegratedFarmSerializer(serializers.ModelSerializer):
    """Serializer for farms with Rotem integration"""
    controllers_count = serializers.SerializerMethodField()
    # Provide fields with names matching the old RotemFarm structure for backward compatibility
    farm_id = serializers.CharField(source='rotem_farm_id', read_only=True)
    farm_name = serializers.CharField(source='name', read_only=True)
    gateway_name = serializers.CharField(source='rotem_gateway_name', read_only=True)
    gateway_alias = serializers.CharField(source='rotem_gateway_alias', read_only=True)
    
    class Meta:
        model = Farm
        fields = [
            'id', 'farm_id', 'farm_name', 'name', 'location',
            'gateway_name', 'gateway_alias', 
            'integration_type', 'integration_status',
            'rotem_username', 'rotem_farm_id', 'rotem_gateway_name', 'rotem_gateway_alias',
            'is_active', 'created_at', 'controllers_count'
        ]
    
    def get_controllers_count(self, obj):
        return obj.rotem_controllers.count()


# Keep legacy serializer for backward compatibility (will be removed later)
class RotemFarmSerializer(serializers.ModelSerializer):
    """Legacy serializer - use IntegratedFarmSerializer instead"""
    controllers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RotemFarm
        fields = ['id', 'farm_id', 'farm_name', 'gateway_name', 'gateway_alias', 'is_active', 'created_at', 'controllers_count']
    
    def get_controllers_count(self, obj):
        return obj.legacy_controllers.count()


class RotemUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = RotemUser
        fields = ['id', 'user_id', 'username', 'display_name', 'email', 'phone_number', 'is_farm_admin', 'is_active', 'last_login']


class RotemScrapeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RotemScrapeLog
        fields = ['id', 'scrape_id', 'status', 'data_points_collected', 'started_at', 'completed_at', 'error_message']


class MLModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModel
        fields = ['id', 'name', 'version', 'model_type', 'is_active', 'accuracy_score', 'training_data_size', 'last_trained', 'created_at']


class RotemDailySummarySerializer(serializers.ModelSerializer):
    controller_name = serializers.CharField(source='controller.controller_name', read_only=True)
    farm_name = serializers.CharField(source='controller.farm.name', read_only=True)
    
    class Meta:
        model = RotemDailySummary
        fields = [
            'id', 'controller', 'controller_name', 'farm_name', 'date',
            'temperature_avg', 'temperature_min', 'temperature_max', 'temperature_data_points',
            'humidity_avg', 'humidity_min', 'humidity_max', 'humidity_data_points',
            'static_pressure_avg', 'static_pressure_min', 'static_pressure_max', 'static_pressure_data_points',
            'wind_speed_avg', 'wind_speed_min', 'wind_speed_max', 'wind_speed_data_points',
            'water_consumption_avg', 'water_consumption_min', 'water_consumption_max', 'water_consumption_data_points',
            'feed_consumption_avg', 'feed_consumption_min', 'feed_consumption_max', 'feed_consumption_data_points',
            'anomalies_count', 'warnings_count', 'errors_count', 'total_data_points',
            'created_at', 'updated_at'
        ]
