from rest_framework import serializers
from .models import RotemDataPoint, MLPrediction, RotemController, RotemFarm, RotemUser, RotemScrapeLog


class RotemDataPointSerializer(serializers.ModelSerializer):
    controller_name = serializers.CharField(source='controller.controller_name', read_only=True)
    farm_name = serializers.CharField(source='controller.farm.farm_name', read_only=True)
    
    class Meta:
        model = RotemDataPoint
        fields = ['id', 'controller', 'controller_name', 'farm_name', 'timestamp', 'data_type', 'value', 'unit', 'quality']


class MLPredictionSerializer(serializers.ModelSerializer):
    controller_name = serializers.CharField(source='controller.controller_name', read_only=True)
    farm_name = serializers.CharField(source='controller.farm.farm_name', read_only=True)
    
    class Meta:
        model = MLPrediction
        fields = ['id', 'controller', 'controller_name', 'farm_name', 'prediction_type', 'predicted_at', 'confidence_score', 'prediction_data', 'is_active']


class RotemControllerSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.farm_name', read_only=True)
    data_points_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RotemController
        fields = ['id', 'controller_id', 'controller_name', 'controller_type', 'is_connected', 'last_seen', 'farm', 'farm_name', 'data_points_count']
    
    def get_data_points_count(self, obj):
        return obj.data_points.count()


class RotemFarmSerializer(serializers.ModelSerializer):
    controllers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RotemFarm
        fields = ['id', 'farm_id', 'farm_name', 'gateway_name', 'gateway_alias', 'is_active', 'created_at', 'controllers_count']
    
    def get_controllers_count(self, obj):
        return obj.controllers.count()


class RotemUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = RotemUser
        fields = ['id', 'user_id', 'username', 'display_name', 'email', 'phone_number', 'is_farm_admin', 'is_active', 'last_login']


class RotemScrapeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RotemScrapeLog
        fields = ['id', 'scrape_id', 'status', 'data_points_collected', 'started_at', 'completed_at', 'error_message']
