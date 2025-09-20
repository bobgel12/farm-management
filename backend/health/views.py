"""
Health check endpoints for production monitoring
"""
from django.http import JsonResponse
from django.db import connection
from django.utils import timezone
import psutil
import os


def health_check(request):
    """Basic health check endpoint"""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'service': 'chicken-house-management',
            'version': '1.0.0'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


def detailed_health_check(request):
    """Detailed health check with system metrics"""
    try:
        # Database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    # System metrics
    try:
        disk_usage = psutil.disk_usage('/')
        memory = psutil.virtual_memory()
        
        system_metrics = {
            'disk_usage_percent': round(disk_usage.percent, 2),
            'memory_usage_percent': round(memory.percent, 2),
            'memory_available_mb': round(memory.available / 1024 / 1024, 2),
            'cpu_percent': round(psutil.cpu_percent(), 2)
        }
    except Exception as e:
        system_metrics = {'error': str(e)}
    
    # Overall status
    overall_status = 'healthy'
    if 'unhealthy' in db_status:
        overall_status = 'unhealthy'
    
    return JsonResponse({
        'status': overall_status,
        'timestamp': timezone.now().isoformat(),
        'service': 'chicken-house-management',
        'version': '1.0.0',
        'database': db_status,
        'system': system_metrics
    })


def readiness_check(request):
    """Kubernetes readiness probe"""
    try:
        # Check if database is accessible
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check if static files are available
        static_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'staticfiles')
        if not os.path.exists(static_root):
            return JsonResponse({'status': 'not_ready'}, status=503)
        
        return JsonResponse({'status': 'ready'})
    except Exception as e:
        return JsonResponse({'status': 'not_ready', 'error': str(e)}, status=503)


def liveness_check(request):
    """Kubernetes liveness probe"""
    return JsonResponse({'status': 'alive', 'timestamp': timezone.now().isoformat()})
