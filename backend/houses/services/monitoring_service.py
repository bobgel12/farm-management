"""
Monitoring service to handle data parsing and snapshot creation from Rotem API responses
"""
from django.utils import timezone
from django.db import transaction
from houses.models import House, HouseMonitoringSnapshot, HouseAlarm
from farms.models import Farm
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service to handle house monitoring data collection and storage"""
    
    def __init__(self):
        self.logger = logger
    
    def safe_float_convert(self, value, default=None):
        """Safely convert value to float"""
        if value is None:
            return default
        try:
            # Handle string values like '- - -', 'N/A', etc.
            if isinstance(value, str):
                value = value.strip()
                if value in ['- - -', 'N/A', '---', '', 'null', 'LangKey_Off']:
                    return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def parse_command_data(self, command_data: Dict[str, Any], house_number: int) -> Dict[str, Any]:
        """
        Parse RNBL_GetCommandData response and extract structured monitoring data
        
        Args:
            command_data: Raw response from RNBL_GetCommandData API
            house_number: House number for this data
            
        Returns:
            Dictionary with parsed monitoring data
        """
        parsed_data = {
            'house_number': house_number,
            'timestamp': timezone.now(),
            'raw_data': command_data,
            'sensor_data': {},
            'general': {},
            'temperature_sensors': {},
            'consumption': {},
            'alarms': [],
            'status': {}
        }
        
        # Extract response object (handle both 'reponseObj' typo and 'responseObj')
        response_obj = command_data.get('reponseObj') or command_data.get('responseObj')
        if not response_obj or not isinstance(response_obj, dict):
            self.logger.warning(f"No response object found in command data for house {house_number}")
            return parsed_data
        
        ds_data = response_obj.get('dsData', {})
        if not ds_data:
            self.logger.warning(f"No dsData found in response for house {house_number}")
            return parsed_data
        
        # Parse General section
        general_data = ds_data.get('General', [])
        for item in general_data:
            if isinstance(item, dict):
                param_name = item.get('ParameterKeyName', '')
                param_value = item.get('ParameterValue', '')
                unit_type = item.get('ParameterUnitType', '')
                
                # Map common parameters
                if param_name == 'Average_Temperature':
                    parsed_data['general']['average_temperature'] = self.safe_float_convert(param_value)
                elif param_name == 'Outside_Temperature':
                    parsed_data['general']['outside_temperature'] = self.safe_float_convert(param_value)
                elif param_name == 'Inside_Humidity':
                    parsed_data['general']['humidity'] = self.safe_float_convert(param_value)
                elif param_name == 'Static_Pressure':
                    parsed_data['general']['static_pressure'] = self.safe_float_convert(param_value)
                elif param_name == 'Set_Temperature':
                    parsed_data['general']['target_temperature'] = self.safe_float_convert(param_value)
                elif param_name == 'Vent_Level':
                    parsed_data['general']['ventilation_level'] = self.safe_float_convert(param_value)
                elif param_name == 'Growth_Day':
                    parsed_data['general']['growth_day'] = self.safe_float_convert(param_value, default=0)
                elif param_name == 'Daily_Water':
                    parsed_data['consumption']['water_consumption'] = self.safe_float_convert(param_value)
                elif param_name == 'Feed_Consumption':
                    parsed_data['consumption']['feed_consumption'] = self.safe_float_convert(param_value)
                elif param_name == 'Current_Level_CFM':
                    parsed_data['general']['airflow_cfm'] = self.safe_float_convert(param_value)
                elif param_name == 'CFM_Percentage':
                    parsed_data['general']['airflow_percentage'] = self.safe_float_convert(param_value)
                elif param_name == 'Current_Birds_Count_In_House':
                    parsed_data['general']['bird_count'] = self.safe_float_convert(param_value, default=0)
                elif param_name == 'Birds_Livability':
                    parsed_data['general']['livability'] = self.safe_float_convert(param_value)
                elif param_name == 'House_Connection_Status':
                    parsed_data['status']['connection_status'] = self.safe_float_convert(param_value, default=0)
        
        # Parse Temperature Sensors
        temp_sensor_data = ds_data.get('TempSensor', [])
        for idx, sensor in enumerate(temp_sensor_data, 1):
            if isinstance(sensor, dict):
                param_name = sensor.get('ParameterKeyName', f'Temperature_Sensor_{idx}')
                param_value = sensor.get('ParameterValue', '')
                param_display = sensor.get('ParameterDisplayName', param_name)
                
                temp_value = self.safe_float_convert(param_value)
                if temp_value is not None:
                    parsed_data['temperature_sensors'][f'sensor_{idx}'] = {
                        'name': param_name,
                        'display_name': param_display,
                        'value': temp_value,
                        'unit': sensor.get('ParameterUnitType', 'UT_Temperature')
                    }
        
        # Parse Consumption section (if not already in General)
        consumption_data = ds_data.get('Consumption', [])
        for item in consumption_data:
            if isinstance(item, dict):
                param_name = item.get('ParameterKeyName', '')
                param_value = item.get('ParameterValue', '')
                
                if param_name == 'Daily_Water' and 'water_consumption' not in parsed_data['consumption']:
                    parsed_data['consumption']['water_consumption'] = self.safe_float_convert(param_value)
                elif param_name == 'Daily_Feed' or param_name == 'Feed_Consumption':
                    if 'feed_consumption' not in parsed_data['consumption']:
                        parsed_data['consumption']['feed_consumption'] = self.safe_float_convert(param_value)
        
        # Parse Alarms
        alarms_data = ds_data.get('Alarms', [])
        for alarm in alarms_data:
            if isinstance(alarm, dict):
                alarm_message = alarm.get('Alarm_Message', '')
                if alarm_message:
                    parsed_data['alarms'].append({
                        'message': alarm_message,
                        'house': alarm.get('Alarm_House', house_number),
                        'room': alarm.get('Alarm_Room', ''),
                        'time': alarm.get('Alarm_Time', ''),
                        'type': self._determine_alarm_type(alarm_message),
                        'severity': self._determine_alarm_severity(alarm_message)
                    })
        
        # Parse Wind data
        wind_data = ds_data.get('Wind', [])
        for item in wind_data:
            if isinstance(item, dict):
                param_name = item.get('ParameterKeyName', '')
                param_value = item.get('ParameterValue', '')
                
                if 'wind_speed' in param_name.lower():
                    parsed_data['sensor_data']['wind_speed'] = self.safe_float_convert(param_value)
                elif 'wind_direction' in param_name.lower():
                    parsed_data['sensor_data']['wind_direction'] = self.safe_float_convert(param_value)
                elif 'wind_chill' in param_name.lower():
                    parsed_data['sensor_data']['wind_chill_temperature'] = self.safe_float_convert(param_value)
        
        # Store all sensor data sections
        parsed_data['sensor_data'] = {
            'temperature_sensors': parsed_data['temperature_sensors'],
            'wind': parsed_data.get('sensor_data', {}),
            'consumption': parsed_data['consumption'],
        }
        
        # Determine alarm status
        parsed_data['status']['alarm_status'] = 'normal'
        if parsed_data['alarms']:
            # Check if any critical alarms
            if any(a.get('severity') == 'critical' for a in parsed_data['alarms']):
                parsed_data['status']['alarm_status'] = 'critical'
            elif any(a.get('severity') in ['high', 'medium'] for a in parsed_data['alarms']):
                parsed_data['status']['alarm_status'] = 'warning'
        
        return parsed_data
    
    def _determine_alarm_type(self, message: str) -> str:
        """Determine alarm type from message"""
        message_lower = message.lower()
        if any(word in message_lower for word in ['temp', 'temperature', 'hot', 'cold']):
            return 'temperature'
        elif any(word in message_lower for word in ['humid', 'moisture']):
            return 'humidity'
        elif any(word in message_lower for word in ['pressure']):
            return 'pressure'
        elif any(word in message_lower for word in ['connect', 'disconnect', 'communication']):
            return 'connection'
        elif any(word in message_lower for word in ['water', 'feed', 'consumption']):
            return 'consumption'
        elif any(word in message_lower for word in ['fan', 'heater', 'equipment', 'device']):
            return 'equipment'
        return 'other'
    
    def _determine_alarm_severity(self, message: str) -> str:
        """Determine alarm severity from message"""
        message_lower = message.lower()
        if any(word in message_lower for word in ['critical', 'emergency', 'danger', 'fatal']):
            return 'critical'
        elif any(word in message_lower for word in ['high', 'severe', 'urgent']):
            return 'high'
        elif any(word in message_lower for word in ['warning', 'alert', 'caution']):
            return 'medium'
        return 'low'
    
    @transaction.atomic
    def create_snapshot(self, farm: Farm, house_number: int, command_data: Dict[str, Any]) -> Optional[HouseMonitoringSnapshot]:
        """
        Create a monitoring snapshot from Rotem command data
        
        Args:
            farm: Farm instance
            house_number: House number
            command_data: Raw command data from Rotem API
            
        Returns:
            Created HouseMonitoringSnapshot instance or None
        """
        try:
            # Get or create house
            house, created = House.objects.get_or_create(
                farm=farm,
                house_number=house_number,
                defaults={
                    'is_active': True,
                    'is_integrated': True,
                    'capacity': 1000,
                    'chicken_in_date': timezone.now().date(),
                }
            )
            
            # Parse the command data
            parsed_data = self.parse_command_data(command_data, house_number)
            
            # Extract key metrics
            general = parsed_data.get('general', {})
            consumption = parsed_data.get('consumption', {})
            status = parsed_data.get('status', {})
            
            # Create snapshot
            snapshot = HouseMonitoringSnapshot.objects.create(
                house=house,
                timestamp=timezone.now(),
                average_temperature=general.get('average_temperature'),
                outside_temperature=general.get('outside_temperature'),
                humidity=general.get('humidity'),
                static_pressure=general.get('static_pressure'),
                target_temperature=general.get('target_temperature'),
                ventilation_level=general.get('ventilation_level'),
                growth_day=int(general.get('growth_day', 0)) if general.get('growth_day') is not None else None,
                bird_count=int(general.get('bird_count', 0)) if general.get('bird_count') is not None else None,
                livability=general.get('livability'),
                water_consumption=consumption.get('water_consumption'),
                feed_consumption=consumption.get('feed_consumption'),
                airflow_cfm=general.get('airflow_cfm'),
                airflow_percentage=general.get('airflow_percentage'),
                connection_status=int(status.get('connection_status', 0)) if status.get('connection_status') is not None else None,
                alarm_status=status.get('alarm_status', 'normal'),
                raw_data=command_data,
                sensor_data=parsed_data.get('sensor_data', {})
            )
            
            # Update house with latest sync time
            house.last_system_sync = timezone.now()
            if general.get('growth_day'):
                house.current_age_days = int(general.get('growth_day', 0))
            house.save()
            
            # Create alarm records
            alarms = parsed_data.get('alarms', [])
            for alarm_data in alarms:
                HouseAlarm.objects.create(
                    snapshot=snapshot,
                    house=house,
                    alarm_type=alarm_data.get('type', 'other'),
                    severity=alarm_data.get('severity', 'medium'),
                    message=alarm_data.get('message', ''),
                    timestamp=timezone.now(),
                    is_active=True,
                    is_resolved=False
                )
            
            self.logger.info(f"Created monitoring snapshot for {house} at {snapshot.timestamp}")
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Error creating snapshot for farm {farm.id}, house {house_number}: {str(e)}")
            return None
    
    def create_snapshots_for_farm(self, farm: Farm, all_house_data: Dict[str, Dict[str, Any]]) -> int:
        """
        Create snapshots for all houses in a farm
        
        Args:
            farm: Farm instance
            all_house_data: Dictionary with house keys and command data values
            
        Returns:
            Number of snapshots created
        """
        created_count = 0
        
        for house_key, house_data in all_house_data.items():
            # Extract house number from key (e.g., 'house_1' -> 1)
            try:
                house_number = int(house_key.replace('house_', ''))
            except (ValueError, AttributeError):
                self.logger.warning(f"Could not extract house number from key: {house_key}")
                continue
            
            snapshot = self.create_snapshot(farm, house_number, house_data)
            if snapshot:
                created_count += 1
        
        return created_count

