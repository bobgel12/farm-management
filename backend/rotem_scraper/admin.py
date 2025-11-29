from django.contrib import admin
from .models import RotemFarm, RotemUser, RotemController, RotemDataPoint, RotemScrapeLog, MLPrediction, MLModel, RotemDailySummary


@admin.register(RotemFarm)
class RotemFarmAdmin(admin.ModelAdmin):
    """Legacy RotemFarm admin - deprecated, use Farm model instead"""
    list_display = ['farm_name', 'gateway_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['farm_name', 'gateway_name']
    
    def has_add_permission(self, request):
        """Prevent adding new RotemFarm entries - use Farm model instead"""
        return False


@admin.register(RotemUser)
class RotemUserAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'username', 'email', 'is_farm_admin', 'is_active', 'last_login']
    list_filter = ['is_farm_admin', 'is_active', 'created_at']
    search_fields = ['display_name', 'username', 'email']


@admin.register(RotemController)
class RotemControllerAdmin(admin.ModelAdmin):
    list_display = ['controller_name', 'controller_id', 'get_farm_name', 'controller_type', 'is_connected', 'last_seen']
    list_filter = ['is_connected', 'controller_type', 'created_at']
    search_fields = ['controller_name', 'controller_id', 'farm__name']
    raw_id_fields = ['farm']
    
    def get_farm_name(self, obj):
        return obj.farm.name if obj.farm else 'N/A'
    get_farm_name.short_description = 'Farm'
    get_farm_name.admin_order_field = 'farm__name'


@admin.register(RotemDataPoint)
class RotemDataPointAdmin(admin.ModelAdmin):
    list_display = ['controller', 'data_type', 'value', 'unit', 'quality', 'timestamp']
    list_filter = ['data_type', 'quality', 'timestamp']
    search_fields = ['controller__controller_name']
    date_hierarchy = 'timestamp'


@admin.register(RotemScrapeLog)
class RotemScrapeLogAdmin(admin.ModelAdmin):
    list_display = ['scrape_id', 'status', 'data_points_collected', 'started_at', 'completed_at']
    list_filter = ['status', 'started_at']
    search_fields = ['scrape_id']
    date_hierarchy = 'started_at'


@admin.register(MLPrediction)
class MLPredictionAdmin(admin.ModelAdmin):
    list_display = ['controller', 'prediction_type', 'confidence_score', 'predicted_at', 'is_active']
    list_filter = ['prediction_type', 'is_active', 'predicted_at']
    search_fields = ['controller__controller_name']
    date_hierarchy = 'predicted_at'


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'model_type', 'is_active', 'accuracy_score', 'last_trained']
    list_filter = ['is_active', 'model_type', 'created_at']
    search_fields = ['name', 'version']


@admin.register(RotemDailySummary)
class RotemDailySummaryAdmin(admin.ModelAdmin):
    list_display = ['controller', 'date', 'total_data_points', 'temperature_avg', 'humidity_avg', 'anomalies_count', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['controller__controller_name']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']