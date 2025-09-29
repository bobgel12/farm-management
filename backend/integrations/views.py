from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from .tasks import run_ml_analysis, run_farm_ml_analysis, sync_and_analyze_farm, generate_daily_report
from .ml_service import EnhancedMLAnalysisService
from farms.models import Farm
from rotem_scraper.models import MLPrediction, RotemController
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_ml_analysis(request):
    """Trigger ML analysis for all integrated farms"""
    try:
        task = run_ml_analysis.delay()
        
        return Response({
            'status': 'success',
            'message': 'ML analysis task started',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Failed to trigger ML analysis: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to start ML analysis: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_farm_ml_analysis(request, farm_id):
    """Trigger ML analysis for a specific farm"""
    try:
        farm = get_object_or_404(Farm, id=farm_id)
        
        if not farm.has_system_integration:
            return Response({
                'status': 'error',
                'message': 'Farm does not have system integration enabled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        task = run_farm_ml_analysis.delay(farm_id)
        
        return Response({
            'status': 'success',
            'message': f'ML analysis task started for farm {farm.name}',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Failed to trigger farm ML analysis: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to start farm ML analysis: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_sync_and_analyze(request, farm_id):
    """Trigger data sync and ML analysis for a specific farm"""
    try:
        farm = get_object_or_404(Farm, id=farm_id)
        
        if not farm.has_system_integration:
            return Response({
                'status': 'error',
                'message': 'Farm does not have system integration enabled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        task = sync_and_analyze_farm.delay(farm_id)
        
        return Response({
            'status': 'success',
            'message': f'Sync and analysis task started for farm {farm.name}',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Failed to trigger sync and analysis: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to start sync and analysis: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ml_predictions(request, farm_id):
    """Get ML predictions for a specific farm"""
    try:
        farm = get_object_or_404(Farm, id=farm_id)
        
        if not farm.has_system_integration:
            return Response({
                'status': 'error',
                'message': 'Farm does not have system integration enabled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get recent predictions (last 24 hours)
        recent_predictions = MLPrediction.objects.filter(
            controller__farm_id=farm.rotem_farm_id,
            predicted_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-predicted_at')
        
        predictions_data = []
        for prediction in recent_predictions:
            predictions_data.append({
                'id': prediction.id,
                'prediction_type': prediction.prediction_type,
                'predicted_at': prediction.predicted_at,
                'confidence_score': prediction.confidence_score,
                'prediction_data': prediction.prediction_data,
                'controller_name': prediction.controller.controller_name if prediction.controller else 'Unknown'
            })
        
        # Group by prediction type
        predictions_by_type = {}
        for pred in predictions_data:
            pred_type = pred['prediction_type']
            if pred_type not in predictions_by_type:
                predictions_by_type[pred_type] = []
            predictions_by_type[pred_type].append(pred)
        
        return Response({
            'status': 'success',
            'farm_name': farm.name,
            'total_predictions': len(predictions_data),
            'predictions_by_type': predictions_by_type,
            'predictions': predictions_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to get ML predictions: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to get ML predictions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ml_summary(request, farm_id):
    """Get ML analysis summary for a specific farm"""
    try:
        farm = get_object_or_404(Farm, id=farm_id)
        
        if not farm.has_system_integration:
            return Response({
                'status': 'error',
                'message': 'Farm does not have system integration enabled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get predictions from last 24 hours
        recent_predictions = MLPrediction.objects.filter(
            controller__farm_id=farm.rotem_farm_id,
            predicted_at__gte=timezone.now() - timedelta(hours=24)
        )
        
        # Calculate summary statistics
        total_predictions = recent_predictions.count()
        anomalies = recent_predictions.filter(prediction_type='anomaly').count()
        failures = recent_predictions.filter(prediction_type='failure').count()
        optimizations = recent_predictions.filter(prediction_type='optimization').count()
        performance = recent_predictions.filter(prediction_type='performance').count()
        
        # Get high-confidence predictions
        high_confidence = recent_predictions.filter(confidence_score__gte=0.8).count()
        
        # Get latest prediction
        latest_prediction = recent_predictions.first()
        latest_prediction_data = None
        if latest_prediction:
            latest_prediction_data = {
                'type': latest_prediction.prediction_type,
                'predicted_at': latest_prediction.predicted_at,
                'confidence_score': latest_prediction.confidence_score,
                'data': latest_prediction.prediction_data
            }
        
        return Response({
            'status': 'success',
            'farm_name': farm.name,
            'summary': {
                'total_predictions': total_predictions,
                'anomalies_detected': anomalies,
                'failure_predictions': failures,
                'optimization_suggestions': optimizations,
                'performance_analyses': performance,
                'high_confidence_predictions': high_confidence,
                'latest_prediction': latest_prediction_data
            },
            'last_updated': timezone.now()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to get ML summary: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to get ML summary: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_global_ml_summary(request):
    """Get global ML analysis summary for all integrated farms"""
    try:
        integrated_farms = Farm.objects.filter(
            has_system_integration=True,
            integration_status='active'
        )
        
        total_farms = integrated_farms.count()
        total_predictions = 0
        total_anomalies = 0
        total_failures = 0
        total_optimizations = 0
        total_performance = 0
        
        farm_summaries = []
        
        for farm in integrated_farms:
            try:
                # Get recent predictions for this farm
                recent_predictions = MLPrediction.objects.filter(
                    controller__farm_id=farm.rotem_farm_id,
                    predicted_at__gte=timezone.now() - timedelta(hours=24)
                )
                
                farm_predictions = recent_predictions.count()
                farm_anomalies = recent_predictions.filter(prediction_type='anomaly').count()
                farm_failures = recent_predictions.filter(prediction_type='failure').count()
                farm_optimizations = recent_predictions.filter(prediction_type='optimization').count()
                farm_performance = recent_predictions.filter(prediction_type='performance').count()
                
                farm_summaries.append({
                    'farm_id': farm.id,
                    'farm_name': farm.name,
                    'integration_type': farm.integration_type,
                    'predictions_count': farm_predictions,
                    'anomalies': farm_anomalies,
                    'failures': farm_failures,
                    'optimizations': farm_optimizations,
                    'performance': farm_performance
                })
                
                total_predictions += farm_predictions
                total_anomalies += farm_anomalies
                total_failures += farm_failures
                total_optimizations += farm_optimizations
                total_performance += farm_performance
                
            except Exception as e:
                logger.error(f"Error getting summary for farm {farm.name}: {str(e)}")
                continue
        
        return Response({
            'status': 'success',
            'global_summary': {
                'total_farms': total_farms,
                'total_predictions': total_predictions,
                'total_anomalies': total_anomalies,
                'total_failures': total_failures,
                'total_optimizations': total_optimizations,
                'total_performance': total_performance
            },
            'farm_summaries': farm_summaries,
            'last_updated': timezone.now()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to get global ML summary: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to get global ML summary: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_daily_report(request):
    """Trigger daily report generation"""
    try:
        task = generate_daily_report.delay()
        
        return Response({
            'status': 'success',
            'message': 'Daily report generation started',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.error(f"Failed to trigger daily report: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to start daily report generation: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)