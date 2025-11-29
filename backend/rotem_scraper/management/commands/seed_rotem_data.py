"""
Management command to seed Rotem test data for Playwright tests.
Creates farms with Rotem integration, controllers, data points, and ML predictions.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from decimal import Decimal

from farms.models import Farm
from organizations.models import Organization
from rotem_scraper.models import (
    RotemController, RotemDataPoint, RotemDailySummary, MLPrediction
)


class Command(BaseCommand):
    help = 'Seed Rotem integration test data for Playwright tests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing Rotem data before seeding',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days of historical data to generate (default: 7)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing Rotem data...')
            MLPrediction.objects.all().delete()
            RotemDailySummary.objects.all().delete()
            RotemDataPoint.objects.all().delete()
            RotemController.objects.filter(controller_id__startswith='seed-').delete()
            Farm.objects.filter(rotem_farm_id__startswith='seed-').delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing seed data'))

        days = options['days']
        self.stdout.write(f'Seeding {days} days of Rotem test data...')

        # Get default organization
        org = Organization.objects.filter(slug='default').first()
        if not org:
            org = Organization.objects.create(
                name='Default Organization',
                slug='default'
            )
            self.stdout.write(f'Created default organization: {org.name}')

        # Create test farms with Rotem integration
        farms_data = [
            {
                'name': 'Sunrise Poultry Farm',
                'rotem_farm_id': 'seed-sunrise-001',
                'location': '123 Farm Road, Rural County',
                'rotem_username': 'sunrise@test.com',
            },
            {
                'name': 'Valley View Farms',
                'rotem_farm_id': 'seed-valley-002',
                'location': '456 Valley Lane, Hillside',
                'rotem_username': 'valley@test.com',
            },
        ]

        created_farms = []
        for farm_data in farms_data:
            farm, created = Farm.objects.get_or_create(
                rotem_farm_id=farm_data['rotem_farm_id'],
                defaults={
                    'organization': org,
                    'name': farm_data['name'],
                    'location': farm_data['location'],
                    'has_system_integration': True,
                    'integration_type': 'rotem',
                    'integration_status': 'active',
                    'rotem_username': farm_data['rotem_username'],
                    'rotem_password': 'test-password',
                    'rotem_gateway_name': f"Gateway-{farm_data['rotem_farm_id']}",
                    'rotem_gateway_alias': f"{farm_data['name']} Gateway",
                    'is_active': True,
                }
            )
            created_farms.append(farm)
            action = 'Created' if created else 'Found existing'
            self.stdout.write(f'{action} farm: {farm.name}')

        # Create controllers for each farm
        controllers = []
        for farm in created_farms:
            for i in range(1, 3):  # 2 controllers per farm
                controller, created = RotemController.objects.get_or_create(
                    controller_id=f"seed-{farm.rotem_farm_id}-ctrl-{i}",
                    defaults={
                        'farm': farm,
                        'controller_name': f'{farm.name} Controller {i}',
                        'controller_type': 'Main' if i == 1 else 'Backup',
                        'is_connected': True,
                        'last_seen': timezone.now(),
                    }
                )
                controllers.append(controller)
                action = 'Created' if created else 'Found existing'
                self.stdout.write(f'  {action} controller: {controller.controller_name}')

        # Generate data points for each controller
        now = timezone.now()
        data_points_created = 0
        
        for controller in controllers:
            for day_offset in range(days):
                for hour in range(0, 24, 2):  # Every 2 hours
                    timestamp = now - timedelta(days=day_offset, hours=hour)
                    
                    for house_num in range(1, 5):  # 4 houses per controller
                        # Temperature data
                        base_temp = 22 + random.uniform(-2, 2)
                        # Add some anomalies for ML testing
                        if random.random() < 0.05:  # 5% chance of anomaly
                            base_temp += random.uniform(5, 10)
                        
                        RotemDataPoint.objects.create(
                            controller=controller,
                            timestamp=timestamp,
                            data_type=f'temperature_house_{house_num}',
                            value=round(base_temp, 1),
                            unit='°C',
                            quality='good' if 18 <= base_temp <= 28 else 'warning'
                        )
                        data_points_created += 1

                        # Humidity data
                        base_humidity = 60 + random.uniform(-10, 10)
                        RotemDataPoint.objects.create(
                            controller=controller,
                            timestamp=timestamp,
                            data_type=f'humidity_house_{house_num}',
                            value=round(base_humidity, 1),
                            unit='%',
                            quality='good' if 50 <= base_humidity <= 70 else 'warning'
                        )
                        data_points_created += 1

                        # Pressure data
                        base_pressure = 1013 + random.uniform(-5, 5)
                        RotemDataPoint.objects.create(
                            controller=controller,
                            timestamp=timestamp,
                            data_type=f'pressure_house_{house_num}',
                            value=round(base_pressure, 1),
                            unit='hPa',
                            quality='good'
                        )
                        data_points_created += 1

        self.stdout.write(f'Created {data_points_created} data points')

        # Generate daily summaries
        summaries_created = 0
        for controller in controllers:
            for day_offset in range(days):
                date = (now - timedelta(days=day_offset)).date()
                
                summary, created = RotemDailySummary.objects.get_or_create(
                    controller=controller,
                    date=date,
                    defaults={
                        'temperature_avg': 22 + random.uniform(-1, 1),
                        'temperature_min': 18 + random.uniform(0, 2),
                        'temperature_max': 26 + random.uniform(-2, 2),
                        'temperature_data_points': 48,
                        'humidity_avg': 60 + random.uniform(-5, 5),
                        'humidity_min': 50 + random.uniform(-5, 5),
                        'humidity_max': 70 + random.uniform(-5, 5),
                        'humidity_data_points': 48,
                        'static_pressure_avg': 1013 + random.uniform(-3, 3),
                        'static_pressure_min': 1008,
                        'static_pressure_max': 1018,
                        'static_pressure_data_points': 48,
                        'anomalies_count': random.randint(0, 3),
                        'warnings_count': random.randint(0, 5),
                        'errors_count': random.randint(0, 1),
                        'total_data_points': 144,
                    }
                )
                if created:
                    summaries_created += 1

        self.stdout.write(f'Created {summaries_created} daily summaries')

        # Generate ML predictions
        predictions_created = 0
        prediction_types = ['anomaly', 'failure', 'optimization', 'performance']
        
        for controller in controllers:
            for pred_type in prediction_types:
                # Create multiple predictions per type
                for i in range(3):
                    timestamp = now - timedelta(hours=i * 8)
                    
                    prediction_data = self._generate_prediction_data(pred_type)
                    
                    MLPrediction.objects.create(
                        controller=controller,
                        prediction_type=pred_type,
                        predicted_at=timestamp,
                        confidence_score=round(random.uniform(0.7, 0.98), 2),
                        prediction_data=prediction_data,
                        is_active=True,
                    )
                    predictions_created += 1

        self.stdout.write(f'Created {predictions_created} ML predictions')

        self.stdout.write(self.style.SUCCESS(
            f'\nSeeding complete!\n'
            f'  Farms: {len(created_farms)}\n'
            f'  Controllers: {len(controllers)}\n'
            f'  Data Points: {data_points_created}\n'
            f'  Daily Summaries: {summaries_created}\n'
            f'  ML Predictions: {predictions_created}'
        ))

    def _generate_prediction_data(self, pred_type):
        """Generate realistic prediction data based on type"""
        if pred_type == 'anomaly':
            return {
                'data_type': random.choice(['temperature', 'humidity', 'pressure']),
                'value': round(random.uniform(30, 35), 1),
                'unit': '°C',
                'timestamp': timezone.now().isoformat(),
                'anomaly_score': round(random.uniform(-0.5, -0.1), 2),
                'severity': random.choice(['low', 'medium', 'high']),
            }
        elif pred_type == 'failure':
            return {
                'failure_probability': round(random.uniform(0.1, 0.4), 2),
                'indicators': {
                    'error_rate': round(random.uniform(0.01, 0.05), 3),
                    'warning_rate': round(random.uniform(0.02, 0.1), 3),
                    'temperature_variance': round(random.uniform(1, 5), 2),
                    'extreme_temperature_rate': round(random.uniform(0, 0.1), 3),
                    'humidity_variance': round(random.uniform(2, 8), 2),
                    'data_gap_rate': round(random.uniform(0, 0.05), 3),
                },
                'predicted_failure_time': (timezone.now() + timedelta(days=random.randint(7, 30))).isoformat(),
                'recommended_actions': [
                    'Schedule preventive maintenance',
                    'Check sensor calibration',
                    'Review recent environmental changes',
                ],
            }
        elif pred_type == 'optimization':
            return {
                'type': random.choice(['temperature', 'humidity', 'ventilation']),
                'current': round(random.uniform(20, 30), 1),
                'optimal_range': [22, 26],
                'action': 'Adjust ventilation settings',
                'priority': random.choice(['low', 'medium', 'high']),
            }
        else:  # performance
            return {
                'performance_score': round(random.uniform(0.7, 0.95), 2),
                'data_completeness': round(random.uniform(0.85, 0.99), 2),
                'efficiency_score': round(random.uniform(0.75, 0.95), 2),
                'total_data_points': random.randint(1000, 5000),
                'good_quality_points': random.randint(900, 4500),
                'warning_quality_points': random.randint(50, 300),
                'error_quality_points': random.randint(0, 50),
                'recommendations': [
                    'Consider upgrading sensor firmware',
                    'Monitor network connectivity',
                ],
            }

