"""
Debug command to check default program status and create if needed
"""
from django.core.management.base import BaseCommand
from farms.models import Program, ProgramTask
from django.db import transaction


class Command(BaseCommand):
    help = 'Debug and ensure default program exists'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate default program even if it exists',
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Debugging default program...")
        
        # Check current state
        all_programs = Program.objects.all()
        self.stdout.write(f"Total programs in database: {all_programs.count()}")
        
        for program in all_programs:
            self.stdout.write(f"  - {program.name} (default: {program.is_default}, active: {program.is_active})")
        
        # Check for default programs
        default_programs = Program.objects.filter(is_default=True)
        self.stdout.write(f"Default programs found: {default_programs.count()}")
        
        active_default_programs = Program.objects.filter(is_default=True, is_active=True)
        self.stdout.write(f"Active default programs found: {active_default_programs.count()}")
        
        if active_default_programs.exists() and not options['force']:
            program = active_default_programs.first()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Default program exists: {program.name} (ID: {program.id})')
            )
            self.stdout.write(f"   Tasks: {program.tasks.count()}")
            return
        
        # Create or recreate default program
        if options['force'] and active_default_programs.exists():
            self.stdout.write("🗑️  Removing existing default program...")
            active_default_programs.delete()
        
        self.stdout.write("🏗️  Creating default program...")
        
        try:
            with transaction.atomic():
                # Create default program
                default_program = Program.objects.create(
                    name="Default Chicken Program",
                    description="Default program for chicken house management",
                    duration_days=40,
                    is_active=True,
                    is_default=True
                )
                
                # Create basic tasks
                self.create_basic_tasks(default_program)
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Successfully created default program: {default_program.name} (ID: {default_program.id})')
                )
                self.stdout.write(f"   Tasks created: {default_program.tasks.count()}")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to create default program: {str(e)}')
            )
            raise

    def create_basic_tasks(self, program):
        """Create basic tasks for the default program"""
        basic_tasks = [
            # Day 0 - Setup
            {
                'day': 0, 'task_type': 'one_time', 'title': 'House Preparation',
                'description': 'Prepare the chicken house for new flock',
                'instructions': '1. Clean and disinfect the house\n2. Check all equipment\n3. Set up feeders and waterers\n4. Check temperature controls',
                'priority': 'critical', 'estimated_duration': 120, 'is_required': True
            },
            {
                'day': 0, 'task_type': 'one_time', 'title': 'Equipment Check',
                'description': 'Check all equipment before flock arrival',
                'instructions': '1. Test heating system\n2. Check ventilation\n3. Test feeders and waterers\n4. Check lighting system',
                'priority': 'critical', 'estimated_duration': 60, 'is_required': True
            },
            
            # Day 1 - Arrival
            {
                'day': 1, 'task_type': 'one_time', 'title': 'Flock Arrival',
                'description': 'Receive and settle new flock',
                'instructions': '1. Count and record number of birds\n2. Check for any sick or injured birds\n3. Provide immediate access to water\n4. Monitor temperature closely',
                'priority': 'critical', 'estimated_duration': 90, 'is_required': True
            },
            
            # Daily tasks
            {
                'day': 1, 'task_type': 'daily', 'title': 'Daily Health Check',
                'description': 'Check flock health and behavior',
                'instructions': '1. Observe bird behavior\n2. Check for signs of illness\n3. Count any dead birds\n4. Record observations',
                'priority': 'high', 'estimated_duration': 30, 'is_required': True
            },
            {
                'day': 1, 'task_type': 'daily', 'title': 'Feed Check',
                'description': 'Check and refill feeders',
                'instructions': '1. Check feed levels\n2. Refill if needed\n3. Check feed quality\n4. Record consumption',
                'priority': 'high', 'estimated_duration': 20, 'is_required': True
            },
            {
                'day': 1, 'task_type': 'daily', 'title': 'Water Check',
                'description': 'Check and clean waterers',
                'instructions': '1. Check water levels\n2. Clean waterers\n3. Check water quality\n4. Record consumption',
                'priority': 'high', 'estimated_duration': 25, 'is_required': True
            },
            
            # Weekly tasks
            {
                'day': 7, 'task_type': 'weekly', 'title': 'Weekly Deep Clean',
                'description': 'Perform weekly deep cleaning',
                'instructions': '1. Remove all bedding\n2. Clean and disinfect floor\n3. Clean feeders and waterers\n4. Add fresh bedding',
                'priority': 'medium', 'estimated_duration': 120, 'is_required': True
            },
            {
                'day': 7, 'task_type': 'weekly', 'title': 'Equipment Maintenance',
                'description': 'Weekly equipment maintenance',
                'instructions': '1. Check all equipment\n2. Clean and lubricate moving parts\n3. Check electrical connections\n4. Record maintenance',
                'priority': 'medium', 'estimated_duration': 60, 'is_required': True
            },
            
            # Final day
            {
                'day': 40, 'task_type': 'one_time', 'title': 'Flock Exit Preparation',
                'description': 'Prepare for flock exit',
                'instructions': '1. Schedule pickup\n2. Prepare birds for transport\n3. Clean and prepare house\n4. Record final weights',
                'priority': 'critical', 'estimated_duration': 90, 'is_required': True
            }
        ]
        
        tasks_created = 0
        for task_data in basic_tasks:
            ProgramTask.objects.create(program=program, **task_data)
            tasks_created += 1
        
        self.stdout.write(f"Created {tasks_created} basic tasks for default program")
