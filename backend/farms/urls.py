from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'farms', views.FarmViewSet, basename='farm')
router.register(r'breeds', views.BreedViewSet, basename='breed')
router.register(r'flocks', views.FlockViewSet, basename='flock')
router.register(r'flock-performance', views.FlockPerformanceViewSet, basename='flock-performance')
router.register(r'flock-comparisons', views.FlockComparisonViewSet, basename='flock-comparison')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Legacy Farm URLs (for backward compatibility)
    path('farms-legacy/', views.FarmListCreateView.as_view(), name='farm-list-create-legacy'),
    path('farms-legacy/<int:pk>/', views.FarmDetailView.as_view(), name='farm-detail-legacy'),
    path('dashboard/', views.farm_dashboard, name='farm-dashboard'),
    
    # Worker URLs
    path('workers/', views.WorkerListCreateView.as_view(), name='worker-list-create'),
    path('workers/<int:pk>/', views.WorkerDetailView.as_view(), name='worker-detail'),
    path('farms/<int:farm_id>/workers/', views.farm_workers, name='farm-workers'),
    
    # Program URLs
    path('programs/', views.ProgramListCreateView.as_view(), name='program-list-create'),
    path('programs/<int:pk>/', views.ProgramDetailView.as_view(), name='program-detail'),
    path('programs/<int:program_id>/tasks/', views.program_tasks, name='program-tasks'),
    path('programs/<int:program_id>/tasks/day/<int:day>/', views.program_tasks_by_day, name='program-tasks-by-day'),
    path('programs/<int:program_id>/copy/', views.copy_program, name='copy-program'),
    path('programs/default/', views.default_program, name='default-program'),
    path('programs/ensure-default/', views.ensure_default_program, name='ensure-default-program'),
    
    # Program Task URLs
    path('program-tasks/', views.ProgramTaskListCreateView.as_view(), name='program-task-list-create'),
    path('program-tasks/<int:pk>/', views.ProgramTaskDetailView.as_view(), name='program-task-detail'),
    
        # Farm with Program URLs (alternative endpoints)
        path('farms-with-programs/', views.FarmWithProgramListCreateView.as_view(), name='farm-with-program-list-create'),
        path('farms-with-programs/<int:pk>/', views.FarmWithProgramDetailView.as_view(), name='farm-with-program-detail'),
        
        # Program Change Management URLs
        path('program-changes/pending/', views.pending_program_changes, name='pending-program-changes'),
        path('program-changes/<int:change_log_id>/handle/', views.handle_program_change, name='handle-program-change'),
        path('programs/<int:program_id>/impact/', views.program_change_impact, name='program-change-impact'),
]
