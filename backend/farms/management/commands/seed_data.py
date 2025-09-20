"""
Django management command to seed the database with sample data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from farms.models import Farm, Worker
from houses.models import House
from tasks.models import Task, RecurringTask
from tasks.task_scheduler import TaskScheduler
import random


class Command(BaseCommand):
    help = 'Seed the database with sample data for farms, houses, and tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )
        parser.add_argument(
            '--farms',
            type=int,
            default=3,
            help='Number of farms to create (default: 3)',
        )
        parser.add_argument(
            '--houses-per-farm',
            type=int,
            default=2,
            help='Number of houses per farm (default: 2)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Task.objects.all().delete()
            RecurringTask.objects.all().delete()
            House.objects.all().delete()
            Worker.objects.all().delete()
            Farm.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        # Create sample farms
        farms = self.create_farms(options['farms'])
        
        # Create workers for each farm
        for farm in farms:
            self.create_workers(farm)
        
        # Create houses for each farm
        for farm in farms:
            houses = self.create_houses(farm, options['houses_per_farm'])
            
            # Generate tasks for each house
            for house in houses:
                self.generate_tasks_for_house(house)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded database with {len(farms)} farms, '
                f'{sum(len(farm.houses.all()) for farm in farms)} houses, '
                f'and {Task.objects.count()} tasks'
            )
        )

    def create_farms(self, num_farms):
        """Create sample farms"""
        farms = []
        farm_names = [
            "Sunny Acres Farm",
            "Green Valley Poultry",
            "Mountain View Chickens",
            "Riverside Farm",
            "Golden Egg Ranch",
            "Happy Hens Farm",
            "Blue Sky Poultry",
            "Valley View Farm"
        ]
        
        for i in range(num_farms):
            name = farm_names[i % len(farm_names)]
            if i > 0:
                name = f"{name} #{i + 1}"
            
            farm = Farm.objects.create(
                name=name,
                location=f"Location {i + 1}",
                contact_person=f"Farmer {i + 1}",
                contact_email=f"farmer{i + 1}@example.com",
                contact_phone=f"+1-555-{1000 + i:04d}",
                is_active=True
            )
            farms.append(farm)
            self.stdout.write(f'Created farm: {farm.name}')
        
        return farms

    def create_workers(self, farm):
        """Create workers for a farm"""
        worker_names = [
            ("John Smith", "john.smith@example.com"),
            ("Jane Doe", "jane.doe@example.com"),
            ("Mike Johnson", "mike.johnson@example.com"),
            ("Sarah Wilson", "sarah.wilson@example.com"),
            ("Tom Brown", "tom.brown@example.com"),
        ]
        
        # Create 2-3 workers per farm
        num_workers = random.randint(2, 3)
        selected_workers = random.sample(worker_names, num_workers)
        
        for name, email in selected_workers:
            Worker.objects.create(
                farm=farm,
                name=name,
                email=email,
                phone=f"+1-555-{random.randint(1000, 9999)}",
                role=random.choice(["Farm Manager", "Worker", "Supervisor"]),
                is_active=True,
                receive_daily_tasks=True
            )
            self.stdout.write(f'Created worker: {name} for {farm.name}')

    def create_houses(self, farm, num_houses):
        """Create houses for a farm"""
        houses = []
        
        for i in range(num_houses):
            # Random start date between 1-30 days ago
            start_date = timezone.now().date() - timedelta(days=random.randint(1, 30))
            
            house = House.objects.create(
                farm=farm,
                house_number=i + 1,
                chicken_in_date=start_date,
                chicken_out_day=random.randint(35, 45),  # Random out day between 35-45 days
                is_active=True
            )
            houses.append(house)
            self.stdout.write(f'Created house: {house.house_number} for {farm.name}')
        
        return houses

    def generate_tasks_for_house(self, house):
        """Generate tasks for a house using the task scheduler"""
        try:
            TaskScheduler.generate_tasks_for_house(house)
            self.stdout.write(f'Generated tasks for house {house.house_number}')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Error generating tasks for house {house.house_number}: {e}')
            )

    def create_sample_recurring_tasks(self):
        """Create sample recurring tasks"""
        recurring_tasks = [
            {
                'name': 'Daily Feeding',
                'description': 'Feed chickens twice daily',
                'task_type': 'Feeding',
                'frequency_days': 1,
                'start_day': 1,
                'end_day': 42,
                'is_active': True
            },
            {
                'name': 'Water Check',
                'description': 'Check and refill water systems',
                'task_type': 'Maintenance',
                'frequency_days': 1,
                'start_day': 1,
                'end_day': 42,
                'is_active': True
            },
            {
                'name': 'Health Check',
                'description': 'Daily health inspection of birds',
                'task_type': 'Health',
                'frequency_days': 1,
                'start_day': 1,
                'end_day': 42,
                'is_active': True
            },
            {
                'name': 'Egg Collection',
                'description': 'Collect eggs from nesting boxes',
                'task_type': 'Collection',
                'frequency_days': 1,
                'start_day': 1,
                'end_day': 42,
                'is_active': True
            },
            {
                'name': 'Weekly Cleaning',
                'description': 'Deep clean the house',
                'task_type': 'Cleaning',
                'frequency_days': 7,
                'start_day': 1,
                'end_day': 42,
                'is_active': True
            }
        ]
        
        for task_data in recurring_tasks:
            RecurringTask.objects.get_or_create(
                name=task_data['name'],
                defaults=task_data
            )
