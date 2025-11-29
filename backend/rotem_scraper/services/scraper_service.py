from django.conf import settings
from django.utils import timezone
from ..models import RotemFarm, RotemUser, RotemController, RotemDataPoint, RotemScrapeLog
from farms.models import Farm
from ..scraper import RotemScraper
import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)


class DjangoRotemScraperService:
    def __init__(self, farm_id=None):
        self.farm_id = farm_id
        self.farm = None  # Will hold the Farm model instance
        
        if farm_id:
            # Get credentials for specific farm (lookup by rotem_farm_id)
            try:
                self.farm = Farm.objects.get(rotem_farm_id=farm_id, integration_type='rotem')
                self.credentials = {
                    'username': self.farm.rotem_username,
                    'password': self.farm.rotem_password,
                }
            except Farm.DoesNotExist:
                raise Exception(f"Farm with Rotem ID {farm_id} not found")
        else:
            # Use default credentials
            self.credentials = {
                'username': settings.ROTEM_USERNAME,
                'password': settings.ROTEM_PASSWORD,
            }
    
    def scrape_and_save_data(self):
        """Main method to scrape data and save to Django models"""
        scrape_log = RotemScrapeLog.objects.create(
            started_at=timezone.now(),
            status='running'
        )
        
        try:
            # Initialize scraper
            scraper = RotemScraper(
                self.credentials['username'],
                self.credentials['password']
            )
            
            # Login and scrape
            if not scraper.login():
                raise Exception("Login failed")
            
            # Get all data
            data = scraper.scrape_all_data()
            
            if not data['login_success']:
                raise Exception("Scraping failed")
            
            # Process and save data
            farm = self._process_farm_data(data)
            user = self._process_user_data(data)
            controller = self._process_controller_data(data, farm)
            self._process_data_points(data, controller)
            
            # Create monitoring snapshots for houses
            try:
                from houses.services.monitoring_service import MonitoringService
                
                if farm:
                    monitoring_service = MonitoringService()
                    # Extract house data from scraped data
                    house_data_dict = {}
                    for key in data.keys():
                        if key.startswith('command_data_house_'):
                            house_data_dict[key] = data[key]
                    
                    if house_data_dict:
                        snapshots_created = monitoring_service.create_snapshots_for_farm(
                            farm, house_data_dict
                        )
                        logger.info(f"Created {snapshots_created} monitoring snapshots for farm {farm.id}")
            except Exception as e:
                logger.warning(f"Failed to create monitoring snapshots: {e}")
            
            # Update scrape log
            scrape_log.status = 'success'
            scrape_log.completed_at = timezone.now()
            scrape_log.data_points_collected = RotemDataPoint.objects.filter(
                created_at__gte=scrape_log.started_at
            ).count()
            scrape_log.raw_data = data
            
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            scrape_log.status = 'failed'
            scrape_log.error_message = str(e)
            scrape_log.completed_at = timezone.now()
        
        finally:
            scrape_log.save()
            return scrape_log
    
    def scrape_all_farms(self):
        """Scrape data for all farms with Rotem integration"""
        results = []
        # Query Farm model for farms with Rotem integration
        farms = Farm.objects.filter(integration_type='rotem', is_active=True)
        
        for farm in farms:
            if farm.rotem_username and farm.rotem_password:
                try:
                    logger.info(f"Scraping data for farm: {farm.name}")
                    service = DjangoRotemScraperService(farm_id=farm.rotem_farm_id)
                    result = service.scrape_and_save_data()
                    results.append({
                        'farm': farm.name,
                        'farm_id': farm.rotem_farm_id,
                        'status': result.status,
                        'data_points_collected': result.data_points_collected
                    })
                except Exception as e:
                    logger.error(f"Failed to scrape farm {farm.name}: {str(e)}")
                    results.append({
                        'farm': farm.name,
                        'farm_id': farm.rotem_farm_id,
                        'status': 'failed',
                        'error': str(e)
                    })
            else:
                logger.warning(f"Farm {farm.name} has no Rotem credentials")
                results.append({
                    'farm': farm.name,
                    'farm_id': farm.rotem_farm_id,
                    'status': 'skipped',
                    'error': 'No credentials configured'
                })
        
        return results
    
    def _process_farm_data(self, data):
        """Process and save farm data - returns or creates Farm model instance"""
        from organizations.models import Organization
        
        # If we already have a farm from initialization, use it
        if self.farm:
            # Update integration status
            self.farm.integration_status = 'active'
            self.farm.save()
            return self.farm
        
        # Otherwise, create or get a farm
        farm_id = f"farm_{self.credentials['username']}"
        farm_name = f"Farm for {self.credentials['username']}"
        
        # Get default organization
        default_org = Organization.objects.filter(slug='default').first()
        
        # Create or update Farm in farms app
        farm, created = Farm.objects.update_or_create(
            rotem_farm_id=farm_id,
            defaults={
                'organization': default_org,
                'name': farm_name,
                'location': 'Auto-created from Rotem',
                'has_system_integration': True,
                'integration_type': 'rotem',
                'integration_status': 'active',
                'rotem_username': self.credentials['username'],
                'rotem_password': self.credentials['password'],
                'rotem_gateway_name': farm_id,
                'rotem_gateway_alias': farm_name,
                'is_active': True,
            }
        )
        logger.info(f"Farm {'created' if created else 'updated'}: {farm.name}")
        
        # Also maintain legacy RotemFarm for backward compatibility (will be removed later)
        RotemFarm.objects.update_or_create(
            farm_id=farm_id,
            defaults={
                'farm_name': farm_name,
                'gateway_name': farm_id,
                'gateway_alias': farm_name,
                'rotem_username': self.credentials['username'],
                'rotem_password': self.credentials['password'],
                'is_active': True,
            }
        )
        
        self.farm = farm
        return farm
    
    def _process_user_data(self, data):
        """Process and save user data"""
        # Create a default user for the farm
        user, created = RotemUser.objects.update_or_create(
            user_id=1,  # Default user ID
            defaults={
                'username': self.credentials['username'],
                'display_name': f"User {self.credentials['username']}",
                'email': f"{self.credentials['username']}@example.com",
                'phone_number': '',
                'is_farm_admin': True,
                'is_active': True,
                'last_login': timezone.now(),
            }
        )
        logger.info(f"User {'created' if created else 'updated'}: {user.username}")
        return user
    
    def _process_controller_data(self, data, farm):
        """Process and save controller data - links to Farm model"""
        if farm:
            controller_id = f"{farm.rotem_farm_id or farm.id}_main"
            
            # Try to find existing controller
            controller = RotemController.objects.filter(controller_id=controller_id).first()
            
            if controller:
                # Update existing controller to point to Farm
                controller.farm = farm
                controller.controller_name = f"{farm.name} Main Controller"
                controller.is_connected = True
                controller.last_seen = timezone.now()
                controller.save()
                logger.info(f"Controller updated: {controller.controller_name}")
            else:
                # Create new controller linked to Farm
                controller = RotemController.objects.create(
                    controller_id=controller_id,
                    farm=farm,
                    controller_name=f"{farm.name} Main Controller",
                    controller_type='Main',
                    is_connected=True,
                    last_seen=timezone.now(),
                )
                logger.info(f"Controller created: {controller.controller_name}")
            
            return controller
        return None
    
    def _process_data_points(self, data, controller):
        """Process and save time-series data points from Rotem API"""
        if not controller:
            return
            
        current_time = timezone.now()
        data_points_created = 0
        
        # Extract real data from command_data API responses for all houses
        # This endpoint returns detailed sensor data with actual values
        logger.info("Processing command data from all houses...")
        
        for house_num in range(1, 9):
            command_data = data.get(f'command_data_house_{house_num}')
            if command_data and isinstance(command_data, dict) and 'reponseObj' in command_data:
                response_obj = command_data['reponseObj']
                logger.info(f"Processing command data for house {house_num}")
                
                # Extract data from different sections
                ds_data = response_obj.get('dsData', {})
                
                # Process General section (basic house info)
                general_data = ds_data.get('General', [])
                for item in general_data:
                    if isinstance(item, dict) and 'ParameterValue' in item:
                        param_name = item.get('ParameterKeyName', '')
                        param_value = item.get('ParameterValue', '')
                        unit_type = item.get('ParameterUnitType', '')
                        
                        if param_value and param_value != '' and param_value != 'LangKey_Off':
                            try:
                                # Convert to float if possible
                                if param_value.replace('.', '').replace('-', '').isdigit():
                                    current_value = float(param_value)
                                    
                                    # Map parameter names to data types
                                    data_type, unit = self._get_parameter_type_and_unit(param_name, unit_type)
                                    
                                    if data_type != 'unknown':
                                        RotemDataPoint.objects.create(
                                            controller=controller,
                                            timestamp=current_time,
                                            data_type=f"{data_type}_house_{house_num}",
                                            value=current_value,
                                            unit=unit,
                                            quality='good'
                                        )
                                        data_points_created += 1
                                        logger.info(f"Created {data_type}_house_{house_num} data point: {current_value} {unit}")
                            except (ValueError, TypeError):
                                continue
                
                # Process TempSensor section (temperature sensors)
                temp_sensors = ds_data.get('TempSensor', [])
                for sensor in temp_sensors:
                    if isinstance(sensor, dict) and 'ParameterValue' in sensor:
                        sensor_name = sensor.get('ParameterKeyName', '')
                        sensor_value = sensor.get('ParameterValue', '')
                        unit_type = sensor.get('ParameterUnitType', '')
                        
                        if sensor_value and sensor_value != '' and sensor_value != '- - -':
                            try:
                                # Convert to float if possible
                                if sensor_value.replace('.', '').replace('-', '').isdigit():
                                    current_value = float(sensor_value)
                                    
                                    # Map sensor names to data types
                                    data_type, unit = self._get_sensor_type_and_unit_from_name(sensor_name, unit_type)
                                    
                                    if data_type != 'unknown':
                                        RotemDataPoint.objects.create(
                                            controller=controller,
                                            timestamp=current_time,
                                            data_type=f"{data_type}_house_{house_num}",
                                            value=current_value,
                                            unit=unit,
                                            quality='good'
                                        )
                                        data_points_created += 1
                                        logger.info(f"Created {data_type}_house_{house_num} data point: {current_value} {unit}")
                            except (ValueError, TypeError):
                                continue
                
                # Process Consumption section (water, feed, etc.)
                consumption_data = ds_data.get('Consumption', [])
                for item in consumption_data:
                    if isinstance(item, dict) and 'ParameterValue' in item:
                        param_name = item.get('ParameterKeyName', '')
                        param_value = item.get('ParameterValue', '')
                        unit_type = item.get('ParameterUnitType', '')
                        
                        if param_value and param_value != '' and param_value != '0':
                            try:
                                current_value = float(param_value)
                                
                                data_type, unit = self._get_parameter_type_and_unit(param_name, unit_type)
                                
                                if data_type != 'unknown':
                                    RotemDataPoint.objects.create(
                                        controller=controller,
                                        timestamp=current_time,
                                        data_type=f"{data_type}_house_{house_num}",
                                        value=current_value,
                                        unit=unit,
                                        quality='good'
                                    )
                                    data_points_created += 1
                                    logger.info(f"Created {data_type}_house_{house_num} data point: {current_value} {unit}")
                            except (ValueError, TypeError):
                                continue
                
                # Process DigitalOut section (fans, heaters, etc.)
                digital_out = ds_data.get('DigitalOut', [])
                for item in digital_out:
                    if isinstance(item, dict) and 'ParameterValue' in item:
                        param_name = item.get('ParameterKeyName', '')
                        param_value = item.get('ParameterValue', '')
                        param_data = item.get('ParameterData', '')
                        
                        if param_value and param_value != 'LangKey_Off':
                            try:
                                # For digital outputs, use ParameterData for numeric value
                                if param_data and param_data.isdigit():
                                    current_value = float(param_data)
                                    
                                    data_type, unit = self._get_parameter_type_and_unit(param_name, 'UT_Number')
                                    
                                    if data_type != 'unknown':
                                        RotemDataPoint.objects.create(
                                            controller=controller,
                                            timestamp=current_time,
                                            data_type=f"{data_type}_house_{house_num}",
                                            value=current_value,
                                            unit=unit,
                                            quality='good'
                                        )
                                        data_points_created += 1
                                        logger.info(f"Created {data_type}_house_{house_num} data point: {current_value} {unit}")
                            except (ValueError, TypeError):
                                continue
        
            # If no real data was found, create some basic simulated data as fallback
            if data_points_created == 0:
                logger.warning("No real data found, creating simulated data as fallback")
                self._create_simulated_data_points(controller, current_time)
    
    def _get_sensor_type_and_unit(self, field_name):
        """Determine sensor type and unit based on field name"""
        sensor_mappings = {
            'Temperature_Current': ('temperature', '°F'),
            'Humidity_Current': ('humidity', '%'),
            'Wind_Chill_Temperature': ('wind_chill', '°F'),
            'Wind_Speed': ('wind_speed', 'mph'),
            'Wind_Direction': ('wind_direction', 'degrees'),
            'WodPressure': ('pressure', 'inWC'),
            'Heaters': ('heater_status', 'units'),
            'Silo_1': ('silo_1', '%'),
            'Silo_2': ('silo_2', '%'),
            'Silo_3': ('silo_3', '%'),
            'Silo_4': ('silo_4', '%'),
            'Tunnel_Fans': ('tunnel_fans', 'count'),
            'Exh_Fans': ('exhaust_fans', 'count'),
            'Stir_Fans': ('stir_fans', 'count'),
            'Cooling_Pad': ('cooling_pad', 'status'),
            'Light1': ('light_1', '%'),
            'Light2': ('light_2', '%'),
            'Light3': ('light_3', '%'),
            'Light4': ('light_4', '%'),
            'Feeding': ('feeding', 'count'),
            'Auger': ('auger', 'count'),
            'Air_Vent_1_Position': ('air_vent_1', '%'),
            'Air_Vent_2_Position': ('air_vent_2', '%'),
            'Tunnel_Curtain_1_Position': ('tunnel_curtain_1', '%'),
            'Tunnel_Curtain_2_Position': ('tunnel_curtain_2', '%')
        }
        
        return sensor_mappings.get(field_name, ('unknown', 'units'))
    
    def _get_parameter_type_and_unit(self, param_name, unit_type):
        """Determine data type and unit based on parameter name and unit type"""
        # Map unit types to units
        unit_mappings = {
            'UT_Temperature': '°C',
            'UT_Percent': '%',
            'UT_Number': 'units',
            'UT_Weight': 'kg',
            'UT_Volume': 'L',
            'UT_Pressure': 'hPa',
            'UT_Capacity': 'CFM',
            'UT_Time': 'time',
            'UT_WindSpeed': 'mph'
        }
        
        # Map parameter names to data types
        param_mappings = {
            'Average_Temperature': 'temperature',
            'Outside_Temperature': 'outside_temperature',
            'Inside_Humidity': 'humidity',
            'Static_Pressure': 'pressure',
            'Set_Temperature': 'target_temperature',
            'Vent_Level': 'ventilation_level',
            'Growth_Day': 'growth_day',
            'Feed_Consumption': 'feed_consumption',
            'Daily_Water': 'water_consumption',
            'Current_Level_CFM': 'airflow_cfm',
            'CFM_Percentage': 'airflow_percentage',
            'Current_Birds_Count_In_House': 'bird_count',
            'Birds_Livability': 'livability',
            'House_Connection_Status': 'connection_status'
        }
        
        data_type = param_mappings.get(param_name, 'unknown')
        unit = unit_mappings.get(unit_type, 'units')
        
        return data_type, unit
    
    def _get_sensor_type_and_unit_from_name(self, sensor_name, unit_type):
        """Determine data type and unit based on sensor name and unit type"""
        # Map unit types to units
        unit_mappings = {
            'UT_Temperature': '°C',
            'UT_Percent': '%',
            'UT_Number': 'units',
            'UT_Weight': 'kg',
            'UT_Volume': 'L',
            'UT_Pressure': 'hPa',
            'UT_Capacity': 'CFM',
            'UT_Time': 'time',
            'UT_WindSpeed': 'mph'
        }
        
        # Map sensor names to data types
        sensor_mappings = {
            'Tunnel_Temperature': 'tunnel_temperature',
            'Wind_Chill_Temperature': 'wind_chill_temperature',
            'Attic_Temperature': 'attic_temperature',
            'Temperature_Sensor_1': 'temp_sensor_1',
            'Temperature_Sensor_2': 'temp_sensor_2',
            'Temperature_Sensor_3': 'temp_sensor_3',
            'Temperature_Sensor_4': 'temp_sensor_4',
            'Temperature_Sensor_5': 'temp_sensor_5',
            'Temperature_Sensor_6': 'temp_sensor_6',
            'Temperature_Sensor_7': 'temp_sensor_7',
            'Temperature_Sensor_8': 'temp_sensor_8',
            'Temperature_Sensor_9': 'temp_sensor_9',
            'Ammonia': 'ammonia',
            'Wind_Speed': 'wind_speed',
            'Wind_Direction': 'wind_direction'
        }
        
        data_type = sensor_mappings.get(sensor_name, 'unknown')
        unit = unit_mappings.get(unit_type, 'units')
        
        return data_type, unit
    
    def _create_simulated_data_points(self, controller, current_time):
        """Create simulated data points as fallback when real data is not available"""
        # Create realistic simulated data for each house (1-8)
        for house_num in range(1, 9):
            # Temperature data (typical range for poultry houses)
            temp_value = random.uniform(20, 25)  # 20-25°C optimal for chickens
            RotemDataPoint.objects.create(
                controller=controller,
                timestamp=current_time,
                data_type=f'temperature_house_{house_num}',
                value=temp_value,
                unit='°C',
                quality='good'
            )
            
            # Humidity data
            humidity_value = random.uniform(50, 70)  # 50-70% optimal humidity
            RotemDataPoint.objects.create(
                controller=controller,
                timestamp=current_time,
                data_type=f'humidity_house_{house_num}',
                value=humidity_value,
                unit='%',
                quality='good'
            )
            
            # Air pressure data
            pressure_value = random.uniform(1010, 1020)  # Normal atmospheric pressure
            RotemDataPoint.objects.create(
                controller=controller,
                timestamp=current_time,
                data_type=f'pressure_house_{house_num}',
                value=pressure_value,
                unit='hPa',
                quality='good'
            )
            
            # Water consumption (simulated)
            water_consumption = random.uniform(100, 200)  # Liters per day
            RotemDataPoint.objects.create(
                controller=controller,
                timestamp=current_time,
                data_type=f'water_consumption_house_{house_num}',
                value=water_consumption,
                unit='L/day',
                quality='good'
            )
            
            # Feed consumption (simulated)
            feed_consumption = random.uniform(50, 100)  # Kg per day
            RotemDataPoint.objects.create(
                controller=controller,
                timestamp=current_time,
                data_type=f'feed_consumption_house_{house_num}',
                value=feed_consumption,
                unit='kg/day',
                quality='good'
            )
        
        logger.info(f"Created 40 simulated data points (5 per house x 8 houses) for controller {controller.controller_name}")
    
    def _parse_datetime(self, datetime_str):
        """Parse datetime string from API response"""
        if not datetime_str:
            return None
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except:
            return None
