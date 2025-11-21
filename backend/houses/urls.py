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
    path('farms/<int:farm_id>/houses/monitoring/all/', views.farm_houses_monitoring_all, name='farm-houses-monitoring-all'),
    path('farms/<int:farm_id>/houses/monitoring/dashboard/', views.farm_houses_monitoring_dashboard, name='farm-houses-monitoring-dashboard'),
]
