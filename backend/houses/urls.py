from django.urls import path
from . import views

urlpatterns = [
    path('houses/', views.HouseListCreateView.as_view(), name='house-list-create'),
    path('houses/<int:pk>/', views.HouseDetailView.as_view(), name='house-detail'),
    path('houses/dashboard/', views.house_dashboard, name='house-dashboard'),
    path('farms/<int:farm_id>/houses/', views.farm_houses, name='farm-houses'),
    path('farms/<int:farm_id>/houses/<int:house_id>/', views.farm_house_detail, name='farm-house-detail'),
    path('farms/<int:farm_id>/task-summary/', views.farm_task_summary, name='farm-task-summary'),
    
    # Monitoring endpoints
    path('houses/<int:house_id>/monitoring/latest/', views.house_monitoring_latest, name='house-monitoring-latest'),
    path('houses/<int:house_id>/monitoring/history/', views.house_monitoring_history, name='house-monitoring-history'),
    path('houses/<int:house_id>/monitoring/stats/', views.house_monitoring_stats, name='house-monitoring-stats'),
    path('houses/<int:house_id>/monitoring/kpis/', views.house_monitoring_kpis, name='house-monitoring-kpis'),
    path('farms/<int:farm_id>/houses/monitoring/all/', views.farm_houses_monitoring_all, name='farm-houses-monitoring-all'),
    path('farms/<int:farm_id>/houses/monitoring/dashboard/', views.farm_houses_monitoring_dashboard, name='farm-houses-monitoring-dashboard'),
    path('farms/<int:farm_id>/houses/monitoring/snapshot/', views.farm_houses_monitoring_snapshot, name='farm-houses-monitoring-snapshot'),
    path('farms/<int:farm_id>/houses/monitoring/refresh/', views.farm_monitoring_refresh, name='farm-monitoring-refresh'),
    
    # Comparison endpoint
    path('houses/comparison/', views.houses_comparison, name='houses-comparison'),
    
    # Detailed house information
    path('houses/<int:house_id>/details/', views.house_details, name='house-details'),
    path(
        'houses/<int:house_id>/heater-history/',
        views.house_heater_history,
        name='house-heater-history',
    ),
    path(
        'houses/<int:house_id>/heater-history/refresh/',
        views.house_heater_history_refresh,
        name='house-heater-history-refresh',
    ),
    path(
        'houses/<int:house_id>/flocks/sync-from-rotem/',
        views.sync_flock_from_rotem,
        name='house-flocks-sync-from-rotem',
    ),
    
    # Device endpoints
    path('houses/<int:house_id>/devices/', views.house_devices, name='house-devices'),
    path('devices/<int:device_id>/', views.device_detail, name='device-detail'),
    path('devices/<int:device_id>/control/', views.device_control, name='device-control'),
    path('devices/<int:device_id>/status-history/', views.device_status_history, name='device-status-history'),
    
    # Control settings endpoints
    path('houses/<int:house_id>/control/', views.house_control_settings, name='house-control-settings'),
    path('houses/<int:house_id>/control/temperature-curve/', views.temperature_curve, name='house-temperature-curve'),
    
    # Configuration endpoints
    path('houses/<int:house_id>/configuration/', views.house_configuration, name='house-configuration'),
    path('houses/<int:house_id>/sensors/', views.house_sensors, name='house-sensors'),
    
    # Water consumption monitoring
    path('houses/<int:house_id>/water/alerts/', views.list_water_alerts, name='list-water-alerts'),
    path('houses/water/alerts/feed/', views.water_alerts_feed, name='water-alerts-feed'),
    path('houses/water/alerts/<int:alert_id>/acknowledge/', views.acknowledge_water_alert, name='ack-water-alert'),
    path('houses/water/alerts/<int:alert_id>/resolve/', views.resolve_water_alert, name='resolve-water-alert'),
    path('houses/water/alerts/<int:alert_id>/snooze/', views.snooze_water_alert, name='snooze-water-alert'),
    path('houses/<int:house_id>/water/forecasts/', views.list_water_forecasts, name='list-water-forecasts'),
    path('houses/<int:house_id>/water/forecasts/generate/', views.generate_water_forecast, name='generate-water-forecasts'),
    path('houses/<int:house_id>/water/detect-anomalies/', views.trigger_water_anomaly_detection, name='trigger-water-anomaly-detection'),
    path('houses/water/detect-anomalies/', views.trigger_water_anomaly_detection, name='trigger-water-anomaly-detection-all'),
    path('houses/water/detection-status/<str:task_id>/', views.check_water_anomaly_detection_status, name='check-water-anomaly-detection-status'),
]
