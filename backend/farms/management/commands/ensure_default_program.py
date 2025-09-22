"""
Django management command to ensure a default program exists
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from farms.models import Program, ProgramTask
from tasks.task_scheduler import TaskScheduler


class Command(BaseCommand):
    help = 'Ensure a default program exists in the database'

    def handle(self, *args, **options):
        # Check if default program already exists
        try:
            default_program = Program.objects.get(is_default=True, is_active=True)
            self.stdout.write(
                self.style.SUCCESS(f'Default program already exists: {default_program.name}')
            )
            return
        except Program.DoesNotExist:
            pass

        # Create default program from existing task scheduler
        self.stdout.write('Creating default program from task scheduler...')
        
        try:
            with transaction.atomic():
                default_program = Program.objects.create(
                    name="Default Chicken Program",
                    description="Default program based on existing task scheduler templates",
                    duration_days=42,  # -1 to 41 days
                    is_active=True,
                    is_default=True
                )
                
                # Convert task scheduler templates to program tasks
                self.create_program_tasks_from_scheduler(default_program)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created default program: {default_program.name}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create default program: {str(e)}')
            )
            raise

    def create_program_tasks_from_scheduler(self, program):
        """Create program tasks from the existing task scheduler templates"""
        tasks_created = 0
        
        try:
            # Use TaskScheduler templates directly
            task_templates = TaskScheduler.TASK_TEMPLATES
            
            for day_offset, tasks in task_templates.items():
                for task_template in tasks:
                    # Map task types to program task types
                    task_type_mapping = {
                        'setup': 'one_time',
                        'daily': 'daily',
                        'special': 'one_time',
                        'exit': 'one_time',
                        'cleanup': 'one_time'
                    }
                    
                    # Map task types to priorities
                    priority_mapping = {
                        'setup': 'critical',
                        'daily': 'medium',
                        'special': 'high',
                        'exit': 'critical',
                        'cleanup': 'low'
                    }
                    
                    program_task_type = task_type_mapping.get(task_template['task_type'], 'daily')
                    priority = priority_mapping.get(task_template['task_type'], 'medium')
                    
                    # Determine estimated duration based on task type
                    duration_mapping = {
                        'setup': 60,  # 1 hour for setup tasks
                        'daily': 30,  # 30 minutes for daily tasks
                        'special': 45,  # 45 minutes for special tasks
                        'exit': 90,  # 1.5 hours for exit tasks
                        'cleanup': 30  # 30 minutes for cleanup tasks
                    }
                    
                    estimated_duration = duration_mapping.get(task_template['task_type'], 30)
                    
                    # Create program task
                    ProgramTask.objects.create(
                        program=program,
                        day=day_offset,
                        task_type=program_task_type,
                        title=task_template['task_name'],
                        description=task_template['description'],
                        instructions=task_template['description'],  # Use description as instructions
                        priority=priority,
                        estimated_duration=estimated_duration,
                        is_required=True,
                        requires_confirmation=False
                    )
                    tasks_created += 1
                    
            self.stdout.write(f'Successfully created {tasks_created} tasks from TaskScheduler templates')
            
        except Exception as e:
            self.stdout.write(f'Warning: Could not load TaskScheduler templates: {e}')
            # Fall back to basic tasks
            tasks_created = self.create_basic_tasks(program)
        
        # Add recurring tasks
        self.add_recurring_tasks_to_program(program)
        
        self.stdout.write(f'Total tasks created: {tasks_created}')

    def add_recurring_tasks_to_program(self, program):
        """Add recurring tasks to the program"""
        recurring_tasks = [
            {
                'day': 0, 'task_type': 'recurring', 'title': 'Generator Check',
                'description': 'Check generator every Monday at 9am',
                'instructions': '1. Check generator fuel level\n2. Test generator start\n3. Check oil level\n4. Record status',
                'priority': 'high', 'estimated_duration': 30, 'is_required': True,
                'recurring_days': [0]  # Monday
            },
            {
                'day': 0, 'task_type': 'recurring', 'title': 'Feed Bin Check',
                'description': 'Check and report feed bin every Monday and Thursday',
                'instructions': '1. Check feed levels\n2. Record consumption\n3. Report to management\n4. Order if needed',
                'priority': 'medium', 'estimated_duration': 20, 'is_required': True,
                'recurring_days': [0, 3]  # Monday and Thursday
            }
        ]
        
        for task_data in recurring_tasks:
            ProgramTask.objects.create(program=program, **task_data)

    def create_basic_tasks(self, program):
        """Create basic tasks for the default program as fallback"""
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
        
        return tasks_created
