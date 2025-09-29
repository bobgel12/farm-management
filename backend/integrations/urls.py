from django.urls import path
from . import views

urlpatterns = [
    # ML Analysis endpoints
    path('ml/trigger-analysis/', views.trigger_ml_analysis, name='trigger_ml_analysis'),
    path('ml/farms/<int:farm_id>/trigger-analysis/', views.trigger_farm_ml_analysis, name='trigger_farm_ml_analysis'),
    path('ml/farms/<int:farm_id>/sync-and-analyze/', views.trigger_sync_and_analyze, name='trigger_sync_and_analyze'),
    path('ml/farms/<int:farm_id>/predictions/', views.get_ml_predictions, name='get_ml_predictions'),
    path('ml/farms/<int:farm_id>/summary/', views.get_ml_summary, name='get_ml_summary'),
    path('ml/global-summary/', views.get_global_ml_summary, name='get_global_ml_summary'),
    path('ml/trigger-daily-report/', views.trigger_daily_report, name='trigger_daily_report'),
]
