from django.urls import path
from . import views

urlpatterns = [
    path('farms/', views.FarmListCreateView.as_view(), name='farm-list-create'),
    path('farms/<int:pk>/', views.FarmDetailView.as_view(), name='farm-detail'),
    path('dashboard/', views.farm_dashboard, name='farm-dashboard'),
    path('workers/', views.WorkerListCreateView.as_view(), name='worker-list-create'),
    path('workers/<int:pk>/', views.WorkerDetailView.as_view(), name='worker-detail'),
    path('farms/<int:farm_id>/workers/', views.farm_workers, name='farm-workers'),
]
