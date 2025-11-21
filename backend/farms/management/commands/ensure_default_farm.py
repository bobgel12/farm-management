"""
Django management command to ensure a default farm with 8 houses exists
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from farms.models import Farm, Program
from houses.models import House
from tasks.task_scheduler import TaskScheduler


class Command(BaseCommand):
    help = 'Ensure a default farm with 8 houses exists in the database'

    def handle(self, *args, **options):
        # Check if default farm already exists
        try:
            default_farm = Farm.objects.get(name="Default Farm", is_active=True)
            self.stdout.write(
                self.style.SUCCESS(f'Default farm already exists: {default_farm.name} ({default_farm.houses.count()} houses)')
            )
            
            # Ensure it has 8 houses
            existing_houses = default_farm.houses.count()
            if existing_houses < 8:
                self.stdout.write(f'Adding {8 - existing_houses} more houses to reach 8 houses...')
                self.create_houses_for_farm(default_farm, existing_houses + 1, 8)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully added houses. Default farm now has {default_farm.houses.count()} houses')
                )
            return
        except Farm.DoesNotExist:
            pass

        # Create default farm
        self.stdout.write('Creating default farm with 8 houses...')
        
        try:
            with transaction.atomic():
                # Get or create default program
                default_program = None
                try:
                    default_program = Program.objects.get(is_default=True, is_active=True)
                except Program.DoesNotExist:
                    self.stdout.write(self.style.WARNING('Default program not found. Farm will be created without a program.'))
                
                # Create default farm
                default_farm = Farm.objects.create(
                    name="Default Farm",
                    location="Default Location",
                    description="Default farm created automatically with 8 houses",
                    contact_person="Farm Manager",
                    contact_phone="123-456-7890",
                    contact_email="manager@defaultfarm.com",
                    program=default_program,
                    is_active=True
                )
                
                self.stdout.write(f'Successfully created default farm: {default_farm.name}')
                
                # Create 8 houses for the default farm
                self.create_houses_for_farm(default_farm, 1, 8)
                
                # Generate tasks for each house
                self.stdout.write('Generating tasks for houses...')
                for house in default_farm.houses.all():
                    tasks_created = TaskScheduler.generate_tasks_for_house(house)
                    self.stdout.write(f'  House {house.house_number}: {len(tasks_created)} tasks generated')
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created default farm with {default_farm.houses.count()} houses'
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create default farm: {str(e)}')
            )
            raise

    def create_houses_for_farm(self, farm, start_number, end_number):
        """Create houses for a farm from start_number to end_number (inclusive)"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Use today's date as the chicken_in_date for all houses
        chicken_in_date = timezone.now().date()
        
        for house_number in range(start_number, end_number + 1):
            # Check if house already exists
            if House.objects.filter(farm=farm, house_number=house_number).exists():
                self.stdout.write(f'  House {house_number} already exists, skipping...')
                continue
            
            # Calculate expected harvest date (typically 40-49 days after chicken_in_date)
            expected_harvest_date = chicken_in_date + timedelta(days=42)
            
            house = House.objects.create(
                farm=farm,
                house_number=house_number,
                capacity=5000,  # Default capacity
                chicken_in_date=chicken_in_date,
                chicken_out_day=42,
                batch_start_date=chicken_in_date,
                expected_harvest_date=expected_harvest_date,
                current_age_days=0,
                is_active=True,
                is_integrated=False
            )
            
            self.stdout.write(f'  Created House {house_number}')

