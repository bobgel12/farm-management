from django.urls import path
from . import views

urlpatterns = [
    path('houses/', views.HouseListCreateView.as_view(), name='house-list-create'),
    path('houses/<int:pk>/', views.HouseDetailView.as_view(), name='house-detail'),
    path('houses/dashboard/', views.house_dashboard, name='house-dashboard'),
    path('farms/<int:farm_id>/houses/', views.farm_houses, name='farm-houses'),
    path('farms/<int:farm_id>/task-summary/', views.farm_task_summary, name='farm-task-summary'),
]
