from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from .tasks import run_ml_analysis, run_farm_ml_analysis, sync_and_analyze_farm, generate_daily_report
from .ml_service import EnhancedMLAnalysisService
from .rotem import RotemIntegration
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_house_sensor_data(request, farm_id):
    """Get real-time sensor data for all houses in a farm"""
    try:
        farm = get_object_or_404(Farm, id=farm_id)
        
        if not farm.has_system_integration or farm.integration_type != 'rotem':
            return Response({
                'status': 'error',
                'message': 'Farm does not have Rotem integration enabled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create Rotem integration instance
        integration = RotemIntegration(farm)
        
        # Get sensor data for all houses
        all_house_data = integration.get_all_sensor_data()
        
        # Process the data to make it more frontend-friendly
        processed_data = {}
        for house_key, house_data in all_house_data.items():
            house_number = house_key.replace('house_', '')
            
            # Extract relevant sensor data from the command data
            sensor_data = {}
            if house_data and isinstance(house_data, dict):
                # Check for both possible keys (reponseObj with typo and responseObj)
                response_obj = house_data.get('reponseObj') or house_data.get('responseObj')
                if response_obj and isinstance(response_obj, dict):
                    ds_data = response_obj.get('dsData', {})
                else:
                    ds_data = {}
            else:
                ds_data = {}
            
            # Extract comprehensive sensor data from all available data sources
            sensor_data = {}
            
            # Helper function to safely convert parameter values to float
            def safe_float_convert(value, default=0):
                if value is None:
                    return default
                try:
                    # Handle string values like '- - -', 'N/A', etc.
                    if isinstance(value, str):
                        value = value.strip()
                        if value in ['- - -', 'N/A', '---', '', 'null']:
                            return default
                    return float(value)
                except (ValueError, TypeError):
                    return default
            
            # Extract temperature data from TempSensor
            temp_sensor_data = ds_data.get('TempSensor', [])
            if temp_sensor_data and len(temp_sensor_data) > 0:
                # Get tunnel temperature (first reading)
                tunnel_temp = temp_sensor_data[0]
                temp_value = safe_float_convert(tunnel_temp.get('ParameterValue', 0))
                
                sensor_data['temperature'] = {
                    'current': temp_value,
                    'unit': '°C',
                    'status': 'Normal'
                }
                
                # Extract all individual temperature readings
                individual_temps = {}
                for i, temp_reading in enumerate(temp_sensor_data):
                    temp_name = temp_reading.get('ParameterKeyName', f'Temp_{i+1}')
                    temp_value = safe_float_convert(temp_reading.get('ParameterValue', 0))
                    individual_temps[temp_name] = {
                        'value': temp_value,
                        'unit': '°C',
                        'display_name': temp_reading.get('ParameterDisplayName', temp_name)
                    }
                
                sensor_data['individual_temperatures'] = individual_temps

            # Extract humidity data
            humidity_data = ds_data.get('Humidity', [])
            if humidity_data and len(humidity_data) > 0:
                humidity_reading = humidity_data[0]
                sensor_data['humidity'] = {
                    'current': safe_float_convert(humidity_reading.get('ParameterValue', 0)),
                    'unit': '%',
                    'status': humidity_reading.get('Status', 'Normal')
                }

            # Extract pressure data (Static Pressure)
            pressure_data = ds_data.get('Pressure', [])
            if pressure_data and len(pressure_data) > 0:
                pressure_reading = pressure_data[0]
                sensor_data['static_pressure'] = {
                    'current': safe_float_convert(pressure_reading.get('ParameterValue', 0)),
                    'unit': 'BAR',
                    'status': pressure_reading.get('Status', 'Normal')
                }

            # Extract CO2 data
            co2_data = ds_data.get('CO2', [])
            if co2_data and len(co2_data) > 0:
                co2_reading = co2_data[0]
                sensor_data['co2'] = {
                    'current': safe_float_convert(co2_reading.get('ParameterValue', 0)),
                    'unit': 'PPM',
                    'status': co2_reading.get('Status', 'Normal')
                }

            # Extract ammonia data
            ammonia_data = ds_data.get('Ammonia', [])
            if ammonia_data and len(ammonia_data) > 0:
                ammonia_reading = ammonia_data[0]
                sensor_data['ammonia'] = {
                    'current': safe_float_convert(ammonia_reading.get('ParameterValue', 0)),
                    'unit': 'PPM',
                    'status': ammonia_reading.get('Status', 'Normal')
                }

            # Extract wind speed and direction
            wind_data = ds_data.get('Wind', [])
            if wind_data and len(wind_data) > 0:
                for wind_reading in wind_data:
                    wind_type = wind_reading.get('ParameterKeyName', '').lower()
                    if 'speed' in wind_type:
                        sensor_data['wind_speed'] = {
                            'current': safe_float_convert(wind_reading.get('ParameterValue', 0)),
                            'unit': 'MPH',
                            'status': wind_reading.get('Status', 'Normal')
                        }
                    elif 'direction' in wind_type:
                        sensor_data['wind_direction'] = {
                            'current': safe_float_convert(wind_reading.get('ParameterValue', 0)),
                            'unit': 'degrees',
                            'status': wind_reading.get('Status', 'Normal')
                        }

            # Extract consumption data (water/feed) - using correct parameter names
            consumption_data = ds_data.get('Consumption', [])
            if consumption_data and len(consumption_data) > 0:
                for consumption_item in consumption_data:
                    param_name = consumption_item.get('ParameterKeyName', '')
                    param_value = safe_float_convert(consumption_item.get('ParameterValue', 0))
                    
                    if param_name == 'Daily_Water':
                        sensor_data['water'] = {
                            'current': param_value,
                            'unit': 'L',
                            'status': 'Normal'
                        }
                    elif param_name == 'Daily_Feed':
                        sensor_data['feed_consumption'] = {
                            'current': param_value,
                            'unit': 'LB',
                            'status': 'Normal'
                        }

            # Extract feed inventory data
            feed_inv_data = ds_data.get('FeedInv', [])
            if feed_inv_data and len(feed_inv_data) > 0:
                silo_inventory = {}
                for i, silo_reading in enumerate(feed_inv_data):
                    silo_name = silo_reading.get('ParameterKeyName', f'Silo_{i+1}')
                    silo_value = safe_float_convert(silo_reading.get('ParameterValue', 0))
                    silo_inventory[silo_name] = {
                        'current': silo_value,
                        'unit': 'LB',
                        'status': 'Normal'
                    }
                sensor_data['feed_inventory'] = silo_inventory

            # Extract average weight data
            avg_weight_data = ds_data.get('AvgWeight', [])
            if avg_weight_data and len(avg_weight_data) > 0:
                weight_reading = avg_weight_data[0]
                sensor_data['avg_weight'] = {
                    'current': safe_float_convert(weight_reading.get('ParameterValue', 0)),
                    'unit': 'LB',
                    'status': 'Normal'
                }

            # Extract system component status from DigitalOut
            digital_out_data = ds_data.get('DigitalOut', [])
            if digital_out_data and len(digital_out_data) > 0:
                system_components = {}
                for component in digital_out_data:
                    comp_name = component.get('ParameterKeyName', '')
                    comp_value = component.get('ParameterValue', 0)
                    comp_status = component.get('Status', 'Off')
                    
                    if comp_name:
                        system_components[comp_name] = {
                            'status': comp_status,
                            'value': comp_value,
                            'unit': component.get('Unit', '')
                        }
                
                sensor_data['system_components'] = system_components

            # Extract control settings from AnalogOut
            analog_out_data = ds_data.get('AnalogOut', [])
            if analog_out_data and len(analog_out_data) > 0:
                control_settings = {}
                for control in analog_out_data:
                    control_name = control.get('ParameterKeyName', '')
                    control_value = safe_float_convert(control.get('ParameterValue', 0))
                    
                    if control_name:
                        control_settings[control_name] = {
                            'current': control_value,
                            'unit': control.get('Unit', '%'),
                            'status': control.get('Status', 'Normal')
                        }
                
                sensor_data['control_settings'] = control_settings

            # Extract ventilation level
            vent_data = ds_data.get('Ventilation', [])
            if vent_data and len(vent_data) > 0:
                vent_reading = vent_data[0]
                sensor_data['ventilation'] = {
                    'level': safe_float_convert(vent_reading.get('ParameterValue', 0)),
                    'unit': '%',
                    'cfm': safe_float_convert(vent_reading.get('CFM', 0)),
                    'status': vent_reading.get('Status', 'Normal')
                }

                # Extract livability data
                livability_data = ds_data.get('Livability', [])
                if livability_data and len(livability_data) > 0:
                    livability_reading = livability_data[0]
                    sensor_data['livability'] = {
                        'percentage': safe_float_convert(livability_reading.get('ParameterValue', 0)),
                        'bird_count': safe_float_convert(livability_reading.get('BirdCount', 0)),
                        'unit': '%',
                        'status': 'Normal'
                    }

                # Extract Growth_Day from General array (correct structure)
                general_data = ds_data.get('General', [])
                growth_day = 0
                
                for general_item in general_data:
                    param_name = general_item.get('ParameterKeyName', '')
                    if param_name == 'Growth_Day':
                        growth_day_str = general_item.get('ParameterValue', '0')
                        try:
                            growth_day = int(growth_day_str)
                            sensor_data['growth_day'] = {
                                'current': growth_day,
                                'unit': 'days',
                                'status': 'Normal'
                            }
                            break
                        except (ValueError, TypeError):
                            sensor_data['growth_day'] = {
                                'current': 0,
                                'unit': 'days',
                                'status': 'Unknown'
                            }
                            break
                
                # If no Growth_Day found, check consumption activity
                if growth_day == 0:
                    consumption_data = ds_data.get('Consumption', [])
                    has_activity = False
                    
                    for consumption_item in consumption_data:
                        param_name = consumption_item.get('ParameterKeyName', '')
                        param_value = safe_float_convert(consumption_item.get('ParameterValue', 0))
                        
                        if param_name == 'Daily_Water' and param_value > 0:
                            has_activity = True
                            break
                        elif param_name == 'Daily_Feed' and param_value > 0:
                            has_activity = True
                            break
                    
                    if has_activity:
                        sensor_data['growth_day'] = {
                            'current': 1,  # Default age for active houses
                            'unit': 'days',
                            'status': 'Estimated'
                        }
                    else:
                        sensor_data['growth_day'] = {
                            'current': 0,
                            'unit': 'days',
                            'status': 'Empty'
                        }
            
            processed_data[house_number] = {
                'house_number': house_number,
                'sensors': sensor_data,
                'last_updated': timezone.now().isoformat(),
                'status': 'active' if sensor_data else 'inactive'
            }
        
        return Response({
            'status': 'success',
            'farm_name': farm.name,
            'farm_id': farm.id,
            'houses': processed_data,
            'total_houses': len(processed_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to get house sensor data for farm {farm_id}: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to get house sensor data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)