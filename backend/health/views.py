"""
Health check endpoints for production monitoring
"""
from django.http import JsonResponse
from django.db import connection
from django.utils import timezone
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
            'version': '1.0.0',
            'database': 'connected',
            'endpoint': '/api/health/',
            'debug': {
                'django_loaded': True,
                'database_engine': connection.vendor,
                'request_method': request.method,
                'request_path': request.path
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
            'endpoint': '/api/health/',
            'debug': {
                'django_loaded': True,
                'error_type': type(e).__name__,
                'request_method': request.method,
                'request_path': request.path
            }
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
    
    # System metrics (simplified without psutil)
    try:
        # Basic system info without psutil
        system_metrics = {
            'status': 'basic_metrics_only',
            'note': 'psutil disabled for compatibility'
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

def simple_health_check(request):
    """Simple health check without database dependency"""
    return JsonResponse({
        'status': 'ok',
        'service': 'chicken-house-management',
        'timestamp': timezone.now().isoformat(),
        'message': 'Service is running'
    })


def default_program_check(request):
    """Check if default program exists and is accessible"""
    try:
        from farms.models import Program
        
        # Check if default program exists
        default_programs = Program.objects.filter(is_default=True, is_active=True)
        
        if default_programs.exists():
            program = default_programs.first()
            return JsonResponse({
                'status': 'ok',
                'default_program_exists': True,
                'program_id': program.id,
                'program_name': program.name,
                'total_tasks': program.tasks.count(),
                'timestamp': timezone.now().isoformat()
            })
        else:
            return JsonResponse({
                'status': 'warning',
                'default_program_exists': False,
                'message': 'No default program found',
                'timestamp': timezone.now().isoformat()
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'default_program_exists': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)
