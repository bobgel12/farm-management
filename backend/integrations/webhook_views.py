import logging

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from integrations.tasks import generate_daily_report, run_ml_analysis
from tasks.email_service import TaskEmailService

logger = logging.getLogger(__name__)


def _validate_cron_secret(request):
    cron_secret = request.headers.get('X-Cron-Secret')
    expected_secret = getattr(settings, 'CRON_SECRET', None) or None
    if expected_secret and cron_secret != expected_secret:
        return Response(
            {'error': 'Invalid or missing cron secret token'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    return None


def _handle_trigger_daily_emails(data):
    force = data.get('force', False)
    farm_id = data.get('farm_id')

    if farm_id:
        from farms.models import Farm

        farm = Farm.objects.get(id=farm_id)
        sent_count, message = TaskEmailService.send_farm_task_reminders(farm, force=force)
        return {
            'status': 'success',
            'message': message,
            'sent_count': sent_count,
            'farm_id': farm_id,
        }

    sent_count = TaskEmailService.send_daily_task_reminders(force=force)
    return {
        'status': 'success',
        'message': f'Successfully sent {sent_count} daily task reminder emails',
        'sent_count': sent_count,
    }


def _handle_trigger_daily_scrape(data):
    from rotem_scraper.services.scraper_service import DjangoRotemScraperService

    farm_id = data.get('farm_id')
    service = DjangoRotemScraperService(farm_id=farm_id if farm_id else None)

    if farm_id:
        scrape_log = service.scrape_and_save_data()
        return {
            'status': 'success',
            'message': f'Data collection completed for farm {farm_id}',
            'scrape_status': scrape_log.status,
            'data_points_collected': scrape_log.data_points_collected,
            'completed_at': scrape_log.completed_at.isoformat() if scrape_log.completed_at else None,
            'error_message': scrape_log.error_message if scrape_log.status != 'success' else None,
        }

    results = service.scrape_all_farms()
    return {
        'status': 'success',
        'message': 'Data collection completed for all farms',
        'results': results,
    }


def _handle_trigger_ml_analysis(_data):
    task = run_ml_analysis.delay()
    return {
        'status': 'success',
        'message': 'ML analysis task started',
        'task_id': task.id,
    }


def _handle_trigger_daily_report(_data):
    task = generate_daily_report.delay()
    return {
        'status': 'success',
        'message': 'Daily report generation started',
        'task_id': task.id,
    }


ACTION_HANDLERS = {
    'trigger_daily_emails': _handle_trigger_daily_emails,
    'trigger_daily_scrape': _handle_trigger_daily_scrape,
    'trigger_ml_analysis': _handle_trigger_ml_analysis,
    'trigger_daily_report': _handle_trigger_daily_report,
}


@api_view(['POST'])
@permission_classes([AllowAny])
def n8n_webhook_dispatcher(request):
    """
    Unified inbound webhook for n8n to trigger webapp actions.

    Body: { "action": "trigger_daily_emails", "farm_id": 5, "force": false }
    Header: X-Cron-Secret (required when CRON_SECRET is set)
    """
    auth_error = _validate_cron_secret(request)
    if auth_error:
        return auth_error

    action = request.data.get('action')
    if not action:
        return Response(
            {'error': 'action is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    handler = ACTION_HANDLERS.get(action)
    if not handler:
        return Response(
            {
                'error': f'Unknown action: {action}',
                'available_actions': list(ACTION_HANDLERS.keys()),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = handler(request.data)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as exc:
        logger.error('n8n inbound webhook action %s failed: %s', action, exc)
        return Response(
            {'status': 'error', 'error': str(exc), 'action': action},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
