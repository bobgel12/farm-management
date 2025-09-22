"""
Django management command to seed the database with sample data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from farms.models import Farm, Worker, Program, ProgramTask
from .program_tasks_data import get_standard_program_tasks, get_extended_program_tasks, get_quick_program_tasks
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
            default=4,
            help='Number of houses per farm (default: 4)',
        )
        parser.add_argument(
            '--workers-per-farm',
            type=int,
            default=3,
            help='Number of workers per farm (default: 3)',
        )
        parser.add_argument(
            '--variety',
            action='store_true',
            help='Create maximum variety in house dates and task statuses',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Task.objects.all().delete()
            RecurringTask.objects.all().delete()
            House.objects.all().delete()
            Worker.objects.all().delete()
            Farm.objects.all().delete()
            ProgramTask.objects.all().delete()
            Program.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            
            # Reset auto-increment sequences
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('farms_farm', 'farms_worker', 'farms_program', 'farms_programtask', 'houses_house', 'tasks_task', 'tasks_recurringtask', 'tasks_emailtask')")
            self.stdout.write('Reset auto-increment sequences')

        # Create sample programs first
        programs = self.create_programs()
        
        # Create sample farms
        farms = self.create_farms(options['farms'], programs)
        
        # Create workers for each farm
        for farm in farms:
            self.create_workers(farm, options['workers_per_farm'])
        
        # Create houses for each farm
        for farm in farms:
            houses = self.create_houses(farm, options['houses_per_farm'], options['variety'])
            
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

    def create_programs(self):
        """Create sample task programs"""
        programs = []
        
        # Standard 40-day program
        standard_program = Program.objects.create(
            name="Standard 40-Day Program",
            description="Standard chicken rearing program for 40 days",
            duration_days=40,
            is_active=True,
            is_default=True
        )
        programs.append(standard_program)
        
        # Extended 45-day program
        extended_program = Program.objects.create(
            name="Extended 45-Day Program",
            description="Extended program for larger chickens, 45 days",
            duration_days=45,
            is_active=True,
            is_default=False
        )
        programs.append(extended_program)
        
        # Quick 35-day program
        quick_program = Program.objects.create(
            name="Quick 35-Day Program",
            description="Fast-track program for smaller chickens, 35 days",
            duration_days=35,
            is_active=True,
            is_default=False
        )
        programs.append(quick_program)
        
        # Create tasks for each program
        self.create_program_tasks(standard_program, get_standard_program_tasks())
        self.create_program_tasks(extended_program, get_extended_program_tasks())
        self.create_program_tasks(quick_program, get_quick_program_tasks())
        
        self.stdout.write(f'Created {len(programs)} programs')
        return programs

    def create_program_tasks(self, program, tasks_data):
        """Create tasks for a program"""
        for task_data in tasks_data:
            ProgramTask.objects.create(program=program, **task_data)
        self.stdout.write(f'Created {len(tasks_data)} tasks for {program.name}')

    def create_farms(self, num_farms, programs):
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
            
            # Assign program to farm (cycle through available programs)
            program = programs[i % len(programs)]
            
            farm = Farm.objects.create(
                name=name,
                location=f"Location {i + 1}",
                contact_person=f"Farmer {i + 1}",
                contact_email=f"farmer{i + 1}@example.com",
                contact_phone=f"+1-555-{1000 + i:04d}",
                program=program,
                is_active=True
            )
            farms.append(farm)
            self.stdout.write(f'Created farm: {farm.name}')
        
        return farms

    def create_workers(self, farm, num_workers):
        """Create workers for a farm with variety"""
        worker_names = [
            ("John Smith", "john.smith@example.com"),
            ("Jane Doe", "jane.doe@example.com"),
            ("Mike Johnson", "mike.johnson@example.com"),
            ("Sarah Wilson", "sarah.wilson@example.com"),
            ("Tom Brown", "tom.brown@example.com"),
            ("Emily Davis", "emily.davis@example.com"),
            ("David Lee", "david.lee@example.com"),
            ("Lisa Chen", "lisa.chen@example.com"),
            ("Mark Wilson", "mark.wilson@example.com"),
            ("Anna Rodriguez", "anna.rodriguez@example.com"),
        ]
        
        # Select workers for this farm
        selected_workers = random.sample(worker_names, min(num_workers, len(worker_names)))
        
        # Define roles with distribution
        roles = ["Farm Manager", "Supervisor", "Worker", "Maintenance", "Health Inspector"]
        role_weights = [0.1, 0.2, 0.5, 0.1, 0.1]  # More workers, fewer managers
        
        for i, (name, email) in enumerate(selected_workers):
            # First worker is usually a manager
            if i == 0:
                role = "Farm Manager"
            else:
                role = random.choices(roles, weights=role_weights)[0]
            
            # Some workers might be inactive
            is_active = random.random() > 0.1  # 90% active
            
            # Some workers might not receive daily tasks
            receive_daily_tasks = random.random() > 0.2  # 80% receive tasks
            
            worker = Worker.objects.create(
                farm=farm,
                name=name,
                email=email,
                phone=f"+1-555-{random.randint(1000, 9999)}",
                role=role,
                is_active=is_active,
                receive_daily_tasks=receive_daily_tasks
            )
            
            # Log worker creation with status
            status_icons = {
                'Farm Manager': '👨‍💼',
                'Supervisor': '👨‍🔧',
                'Worker': '👷',
                'Maintenance': '🔧',
                'Health Inspector': '👩‍⚕️'
            }
            
            active_status = "✅" if is_active else "❌"
            email_status = "📧" if receive_daily_tasks else "📵"
            
            self.stdout.write(
                f'Created worker: {name} for {farm.name} '
                f'{status_icons.get(role, "👤")} {role} {active_status} {email_status}'
            )

    def create_houses(self, farm, num_houses, variety_mode=False):
        """Create houses for a farm with variety of dates and statuses"""
        houses = []
        
        for i in range(num_houses):
            # Create variety of house statuses and dates
            if variety_mode:
                # In variety mode, cycle through different scenarios to ensure variety
                scenario_index = i % 7  # Cycle through 7 different scenarios
                house_scenarios = [
                    # Scenario 1: New house (chickens just arrived)
                    {
                        'days_ago': random.randint(0, 2),
                        'out_day': random.randint(40, 45),
                        'status': 'setup'
                    },
                    # Scenario 2: Early care phase (1-7 days)
                    {
                        'days_ago': random.randint(3, 7),
                        'out_day': random.randint(40, 45),
                        'status': 'early_care'
                    },
                    # Scenario 3: Growth phase (8-20 days)
                    {
                        'days_ago': random.randint(8, 20),
                        'out_day': random.randint(40, 45),
                        'status': 'growth'
                    },
                    # Scenario 4: Mature phase (21-35 days)
                    {
                        'days_ago': random.randint(21, 35),
                        'out_day': random.randint(40, 45),
                        'status': 'mature'
                    },
                    # Scenario 5: Near completion (36-40 days)
                    {
                        'days_ago': random.randint(36, 40),
                        'out_day': random.randint(40, 45),
                        'status': 'near_completion'
                    },
                    # Scenario 6: Empty house (chickens already out)
                    {
                        'days_ago': random.randint(45, 60),
                        'out_day': random.randint(40, 45),
                        'status': 'empty'
                    },
                    # Scenario 7: Future house (chickens arriving soon)
                    {
                        'days_ago': -random.randint(1, 7),  # Future date
                        'out_day': random.randint(40, 45),
                        'status': 'preparation'
                    }
                ]
                scenario = house_scenarios[scenario_index]
            else:
                # Normal mode - randomly select scenarios
                house_scenarios = [
                    # Scenario 1: New house (chickens just arrived)
                    {
                        'days_ago': random.randint(0, 2),
                        'out_day': random.randint(40, 45),
                        'status': 'setup'
                    },
                    # Scenario 2: Early care phase (1-7 days)
                    {
                        'days_ago': random.randint(3, 7),
                        'out_day': random.randint(40, 45),
                        'status': 'early_care'
                    },
                    # Scenario 3: Growth phase (8-20 days)
                    {
                        'days_ago': random.randint(8, 20),
                        'out_day': random.randint(40, 45),
                        'status': 'growth'
                    },
                    # Scenario 4: Mature phase (21-35 days)
                    {
                        'days_ago': random.randint(21, 35),
                        'out_day': random.randint(40, 45),
                        'status': 'mature'
                    },
                    # Scenario 5: Near completion (36-40 days)
                    {
                        'days_ago': random.randint(36, 40),
                        'out_day': random.randint(40, 45),
                        'status': 'near_completion'
                    },
                    # Scenario 6: Empty house (chickens already out)
                    {
                        'days_ago': random.randint(45, 60),
                        'out_day': random.randint(40, 45),
                        'status': 'empty'
                    },
                    # Scenario 7: Future house (chickens arriving soon)
                    {
                        'days_ago': -random.randint(1, 7),  # Future date
                        'out_day': random.randint(40, 45),
                        'status': 'preparation'
                    }
                ]
                scenario = random.choice(house_scenarios)
            
            # Calculate dates
            if scenario['days_ago'] >= 0:
                start_date = timezone.now().date() - timedelta(days=scenario['days_ago'])
            else:
                start_date = timezone.now().date() + timedelta(days=abs(scenario['days_ago']))
            
            # Calculate out date
            out_date = start_date + timedelta(days=scenario['out_day'])
            
            # Determine if house is active based on status
            is_active = scenario['status'] not in ['empty', 'preparation']
            
            house = House.objects.create(
                farm=farm,
                house_number=i + 1,
                chicken_in_date=start_date,
                chicken_out_date=out_date if scenario['status'] == 'empty' else None,
                chicken_out_day=scenario['out_day'],
                is_active=is_active
            )
            houses.append(house)
            
            # Log house creation with status
            status_emoji = {
                'setup': '🏗️',
                'early_care': '🐣',
                'growth': '🌱',
                'mature': '🐔',
                'near_completion': '📦',
                'empty': '🏠',
                'preparation': '⏳'
            }
            
            self.stdout.write(
                f'Created house: {house.house_number} for {farm.name} '
                f'{status_emoji.get(scenario["status"], "🏠")} '
                f'({scenario["status"].replace("_", " ").title()}) - '
                f'Day {house.current_day if house.current_day is not None else "N/A"}'
            )
        
        return houses

    def generate_tasks_for_house(self, house):
        """Generate tasks for a house using the task scheduler"""
        try:
            TaskScheduler.generate_tasks_for_house(house)
            
            # Add variety to task completion statuses
            self.add_task_status_variety(house)
            
            self.stdout.write(f'Generated tasks for house {house.house_number}')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Error generating tasks for house {house.house_number}: {e}')
            )

    def add_task_status_variety(self, house):
        """Add variety to task completion statuses based on house age and status"""
        if not house.is_active:
            return
            
        current_day = house.current_day
        if current_day is None:
            return
            
        # Get all tasks for this house
        all_tasks = Task.objects.filter(house=house)
        
        if not all_tasks.exists():
            return
            
        # Determine completion rates based on house status and age
        completion_scenarios = {
            'setup': 0.1,      # Very few tasks completed in setup
            'early_care': 0.3, # Some tasks completed in early care
            'growth': 0.6,     # Most tasks completed in growth
            'mature': 0.8,     # Almost all tasks completed in mature
            'near_completion': 0.9, # Nearly all tasks completed
            'empty': 1.0,      # All tasks completed for empty houses
            'preparation': 0.0  # No tasks completed for future houses
        }
        
        # Get house status (simplified logic)
        if current_day <= 2:
            status = 'setup'
        elif current_day <= 7:
            status = 'early_care'
        elif current_day <= 20:
            status = 'growth'
        elif current_day <= 35:
            status = 'mature'
        elif current_day <= 40:
            status = 'near_completion'
        else:
            status = 'empty'
            
        completion_rate = completion_scenarios.get(status, 0.5)
        
        # Mark tasks as completed based on completion rate
        tasks_to_complete = int(len(all_tasks) * completion_rate)
        completed_tasks = random.sample(list(all_tasks), min(tasks_to_complete, len(all_tasks)))
        
        for task in completed_tasks:
            # Mark as completed
            task.is_completed = True
            
            # Add completion details
            if random.random() < 0.7:  # 70% chance to have completion details
                task.completed_by = random.choice([
                    'John Smith', 'Jane Doe', 'Mike Johnson', 
                    'Sarah Wilson', 'Tom Brown', 'System'
                ])
                
                # Add completion notes based on task type
                notes_templates = {
                    'Feeding': [
                        'Completed morning feeding routine',
                        'All feeders checked and refilled',
                        'Feeding schedule maintained',
                        'Feed quality verified'
                    ],
                    'Health': [
                        'Health inspection completed',
                        'No issues found during check',
                        'All birds appear healthy',
                        'Temperature and humidity normal'
                    ],
                    'Maintenance': [
                        'Equipment checked and functioning',
                        'Water system operating normally',
                        'Ventilation system working properly',
                        'All systems operational'
                    ],
                    'Cleaning': [
                        'House cleaned and sanitized',
                        'Waste removed and disposed',
                        'Disinfection completed',
                        'House ready for next cycle'
                    ]
                }
                
                task_type = getattr(task, 'task_type', 'Maintenance')
                notes_options = notes_templates.get(task_type, ['Task completed successfully'])
                task.notes = random.choice(notes_options)
            
            # Set completion date (randomly within the last few days)
            days_ago = random.randint(0, min(current_day, 7))
            task.completed_at = timezone.now() - timedelta(days=days_ago)
            task.save()
        
        # Log completion statistics
        completed_count = len(completed_tasks)
        total_count = len(all_tasks)
        self.stdout.write(
            f'  → Marked {completed_count}/{total_count} tasks as completed '
            f'({completion_rate:.1%} completion rate) for house {house.house_number}'
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
