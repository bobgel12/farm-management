"""
Task scheduling logic for chicken house management
"""
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Task, RecurringTask


class TaskScheduler:
    """Handles automatic task generation based on chicken age"""
    
    TASK_TEMPLATES = {
        -1: [  # Day -1: House Setup
            {
                'task_name': 'Open heater pipe lock',
                'description': 'Open heater pipe lock',
                'task_type': 'setup'
            },
            {
                'task_name': 'Turn heater (24 hours ahead)',
                'description': 'Turn heater 24 hours ahead before chicken is in. Before turning heat, check if the heat line is down.',
                'task_type': 'setup'
            },
            {
                'task_name': 'Turn water on',
                'description': 'Turn water on',
                'task_type': 'setup'
            },
            {
                'task_name': 'Check water line',
                'description': 'Check water line',
                'task_type': 'setup'
            },
            {
                'task_name': 'Replace filter',
                'description': 'Replace filter',
                'task_type': 'setup'
            },
            {
                'task_name': 'Set water pressure to 6 half turns',
                'description': 'Set water pressure to 6 half turns',
                'task_type': 'setup'
            },
            {
                'task_name': 'Set water line height to 6 full turns',
                'description': 'Set water line height to 6 full turns',
                'task_type': 'setup'
            },
            {
                'task_name': 'Place 16 plastic tray feeds',
                'description': 'Place 16 plastic tray feeds (5 load per tray) on single feed side',
                'task_type': 'setup'
            },
            {
                'task_name': 'Set up turbo',
                'description': 'Set up turbo',
                'task_type': 'setup'
            },
            {
                'task_name': 'Lock mid house feed line',
                'description': 'Lock mid house feed line',
                'task_type': 'setup'
            },
            {
                'task_name': 'Run feed line to full',
                'description': 'Run feed line to full',
                'task_type': 'setup'
            }
        ],
        0: [  # Day 0: Chicken Arrival
            {
                'task_name': 'Chicken is in',
                'description': 'Chicken is in',
                'task_type': 'daily'
            },
            {
                'task_name': 'Check water line has water all the way to the end',
                'description': 'Check water line has water all the way to the end',
                'task_type': 'daily'
            },
            {
                'task_name': 'Check heater is running',
                'description': 'Check heater is running',
                'task_type': 'daily'
            },
            {
                'task_name': 'Check feed is full',
                'description': 'Check feed is full',
                'task_type': 'daily'
            }
        ],
        1: [  # Day 1: Initial Care
            {
                'task_name': 'Increase water pressure by 1 half turn',
                'description': 'Increase water pressure by 1 half turn',
                'task_type': 'daily'
            },
            {
                'task_name': 'Death chicken pickup',
                'description': 'Death chicken pickup (1 per 2 days)',
                'task_type': 'daily'
            },
            {
                'task_name': 'Set up and turn on feed setup',
                'description': 'Set up and turn on feed setup',
                'task_type': 'daily'
            },
            {
                'task_name': 'Turn on feed manually (morning)',
                'description': 'Turn on feed manually (morning)',
                'task_type': 'daily'
            },
            {
                'task_name': 'Turn on feed manually (afternoon)',
                'description': 'Turn on feed manually (afternoon)',
                'task_type': 'daily'
            }
        ],
        7: [  # Day 7: Transition
            {
                'task_name': 'Close turbo feed, push out',
                'description': 'Close turbo feed, push out',
                'task_type': 'daily'
            },
            {
                'task_name': 'Close curtains (front and back)',
                'description': 'Close curtains (front and back)',
                'task_type': 'daily'
            }
        ],
        8: [  # Day 8: Full House Operations
            {
                'task_name': 'Increase water pressure by 1 half turn',
                'description': 'Increase water pressure by 1 half turn',
                'task_type': 'daily'
            },
            {
                'task_name': 'Turn on feed and water to full house',
                'description': 'Turn on feed and water to full house',
                'task_type': 'daily'
            },
            {
                'task_name': 'Turn feed to 3/4 of front and back side',
                'description': 'Turn feed to 3/4 of front and back side so that at night automatic run can still trigger',
                'task_type': 'daily'
            },
            {
                'task_name': 'Turn on heat 1, 2, 7, 8',
                'description': 'Turn on heat 1, 2, 7, 8',
                'task_type': 'daily'
            },
            {
                'task_name': 'Open separator on 2 sides',
                'description': 'Open separator on 2 sides so chickens can spread out',
                'task_type': 'daily'
            },
            {
                'task_name': 'Turn feed on automatic on controller',
                'description': 'Turn feed on automatic on controller',
                'task_type': 'daily'
            }
        ],
        9: [  # Day 9: Monitoring
            {
                'task_name': 'Check feeder motor on last pan and clean out',
                'description': 'Check feeder motor on last pan and clean out to make sure feed runs for the line 2 times daily (early morning and end of day)',
                'task_type': 'daily'
            },
            {
                'task_name': 'Check if chickens spread out evenly',
                'description': 'Check if chickens spread out evenly, then close separator if needed',
                'task_type': 'daily'
            }
        ],
        10: [  # Day 10: Monitoring
            {
                'task_name': 'Check feeder motor on last pan and clean out',
                'description': 'Check feeder motor on last pan and clean out to make sure feed runs for the line 2 times daily (early morning and end of day)',
                'task_type': 'daily'
            },
            {
                'task_name': 'Check if chickens spread out evenly',
                'description': 'Check if chickens spread out evenly, then close separator if needed',
                'task_type': 'daily'
            }
        ],
        12: [  # Day 12: Cleanup
            {
                'task_name': 'Clean up turbo line',
                'description': 'Clean up turbo line (make it to ceiling)',
                'task_type': 'daily'
            }
        ],
        13: [  # Day 13: Feeder Adjustment
            {
                'task_name': 'Raise feeder line',
                'description': 'Raise feeder line so that the pan doesn\'t touch the ground, level the feeder line',
                'task_type': 'daily'
            }
        ],
        14: [  # Day 14: Water Pressure Increase
            {
                'task_name': 'Increase water pressure by 1 half turn',
                'description': 'Increase water pressure by 1 half turn (repeats every 6 days: 20, 26, 32, 38)',
                'task_type': 'daily'
            }
        ],
        20: [  # Day 20: Coolpad Preparation
            {
                'task_name': 'Turn water on coolpad',
                'description': 'Turn water on coolpad',
                'task_type': 'daily'
            },
            {
                'task_name': 'Increase water pressure by 1 half turn',
                'description': 'Increase water pressure by 1 half turn (repeats every 6 days: 14, 20, 26, 32, 38)',
                'task_type': 'daily'
            }
        ],
        21: [  # Day 21: Coolpad Activation
            {
                'task_name': 'Turn on coolpad breaker',
                'description': 'Turn on coolpad breaker',
                'task_type': 'daily'
            },
            {
                'task_name': 'Turn water on coolpad',
                'description': 'Turn water on coolpad',
                'task_type': 'daily'
            },
            {
                'task_name': 'Turn controller coolpad on auto',
                'description': 'Turn controller coolpad on auto',
                'task_type': 'daily'
            }
        ],
        26: [  # Day 26: Water Pressure
            {
                'task_name': 'Increase water pressure by 1 half turn',
                'description': 'Increase water pressure by 1 half turn (repeats every 6 days: 14, 20, 26, 32, 38)',
                'task_type': 'daily'
            }
        ],
        32: [  # Day 32: Water Pressure
            {
                'task_name': 'Increase water pressure by 1 half turn',
                'description': 'Increase water pressure by 1 half turn (repeats every 6 days: 14, 20, 26, 32, 38)',
                'task_type': 'daily'
            }
        ],
        35: [  # Day 35: Exit Planning
            {
                'task_name': 'Confirm chicken out schedule',
                'description': 'Keep asking for chicken out schedule for each house (both date and time)',
                'task_type': 'special'
            }
        ],
        38: [  # Day 38: Water Pressure
            {
                'task_name': 'Increase water pressure by 1 half turn',
                'description': 'Increase water pressure by 1 half turn (repeats every 6 days: 14, 20, 26, 32, 38)',
                'task_type': 'daily'
            }
        ],
        39: [  # Day 39: Pre-Exit Preparation
            {
                'task_name': 'Turn water pressure 2 half circles',
                'description': 'Turn water pressure 2 half circles',
                'task_type': 'exit'
            }
        ],
        40: [  # Day 40: Chicken Exit Day
            {
                'task_name': 'Turn off feeder (12 hours before)',
                'description': '12 hours before chicken out time: Turn off feeder',
                'task_type': 'exit'
            },
            {
                'task_name': 'Clean out auger and feeder line (10 hours before)',
                'description': '10 hours before chicken out: Clean out auger and feeder line, make sure no feed left on the line',
                'task_type': 'exit'
            },
            {
                'task_name': 'Raise feeder line up (6 hours before)',
                'description': '6 hours before chicken out: Raise feeder line up (Make sure pan is empty)',
                'task_type': 'exit'
            },
            {
                'task_name': 'Turn off heater and raise up',
                'description': 'Turn off heater (both breaker and controller) then raise heater up',
                'task_type': 'exit'
            },
            {
                'task_name': 'Turn off water line and raise up (1 hour before)',
                'description': '1 hour before chicken out: Turn off water line and raise the water line up',
                'task_type': 'exit'
            },
            {
                'task_name': 'Turn on water line on front of house',
                'description': 'Turn on water line on front of house',
                'task_type': 'exit'
            },
            {
                'task_name': 'Turn off tunnel fan, light 3 hours after',
                'description': 'Turn off tunnel fan, light 3 hours after chicken out',
                'task_type': 'exit'
            }
        ],
        41: [  # Day 41: Post-Exit Cleanup
            {
                'task_name': 'Collect death chickens that are left',
                'description': 'Collect death chickens that are left',
                'task_type': 'cleanup'
            }
        ]
    }

    @classmethod
    def generate_tasks_for_house(cls, house):
        """Generate all tasks for a house based on its chicken in date"""
        tasks = []
        
        # Generate tasks for each day from -1 to 41
        for day_offset in range(-1, 42):
            if day_offset in cls.TASK_TEMPLATES:
                for task_template in cls.TASK_TEMPLATES[day_offset]:
                    task, created = Task.objects.get_or_create(
                        house=house,
                        day_offset=day_offset,
                        task_name=task_template['task_name'],
                        defaults={
                            'description': task_template['description'],
                            'task_type': task_template['task_type']
                        }
                    )
                    tasks.append(task)
        
        # Generate recurring tasks for days 1-7 (daily feed tasks)
        for day_offset in range(1, 8):
            if day_offset != 1:  # Day 1 already has feed tasks
                task, created = Task.objects.get_or_create(
                    house=house,
                    day_offset=day_offset,
                    task_name='Turn on feed manually (morning)',
                    defaults={
                        'description': 'Turn on feed manually (morning)',
                        'task_type': 'daily'
                    }
                )
                tasks.append(task)
                
                task, created = Task.objects.get_or_create(
                    house=house,
                    day_offset=day_offset,
                    task_name='Turn on feed manually (afternoon)',
                    defaults={
                        'description': 'Turn on feed manually (afternoon)',
                        'task_type': 'daily'
                    }
                )
                tasks.append(task)
        
        # Generate recurring tasks for days 9-12 (monitoring tasks)
        for day_offset in range(9, 13):
            if day_offset not in [9, 10, 12]:  # These days already have specific tasks
                task, created = Task.objects.get_or_create(
                    house=house,
                    day_offset=day_offset,
                    task_name='Check feeder motor on last pan and clean out',
                    defaults={
                        'description': 'Check feeder motor on last pan and clean out to make sure feed runs for the line 2 times daily (early morning and end of day)',
                        'task_type': 'daily'
                    }
                )
                tasks.append(task)
        
        return tasks

    @classmethod
    def get_tasks_for_day(cls, house, day_offset):
        """Get all tasks for a specific day"""
        return Task.objects.filter(house=house, day_offset=day_offset)

    @classmethod
    def get_today_tasks(cls, house):
        """Get tasks for today based on house's age_days (prefers Rotem age, fallback to calculated)"""
        age_days = house.age_days
        if age_days is None:
            return Task.objects.none()
        return cls.get_tasks_for_day(house, age_days)

    @classmethod
    def get_upcoming_tasks(cls, house, days_ahead=7):
        """Get upcoming tasks for the next N days"""
        age_days = house.age_days
        if age_days is None:
            return Task.objects.none()
        
        end_day = min(age_days + days_ahead, 41)
        return Task.objects.filter(
            house=house,
            day_offset__range=[age_days, end_day]
        ).order_by('day_offset', 'task_name')
    
    @classmethod
    def generate_tasks_from_program(cls, house, program, force_regenerate=False):
        """Generate tasks for a house from a Program's ProgramTask templates"""
        from farms.models import ProgramTask, Program
        
        if not program:
            raise ValueError("Program is required to generate tasks")
        
        # Check if tasks already exist
        existing_tasks_count = Task.objects.filter(house=house).count()
        if existing_tasks_count > 0 and not force_regenerate:
            # Tasks already exist, return existing tasks
            return list(Task.objects.filter(house=house))
        
        # If force_regenerate, delete existing tasks first
        if force_regenerate and existing_tasks_count > 0:
            Task.objects.filter(house=house).delete()
        
        tasks = []
        
        # Get all ProgramTask objects for this program
        program_tasks = ProgramTask.objects.filter(
            program=program,
            is_required=True  # Only generate required tasks by default
        ).order_by('day', 'priority', 'title')
        
        if not program_tasks.exists():
            # If no program tasks, fall back to default templates
            return cls.generate_tasks_for_house(house)
        
        # Calculate chicken_in_date if not set
        chicken_in_date = house.chicken_in_date
        if not chicken_in_date:
            # Use current date as default
            chicken_in_date = timezone.now().date()
            house.chicken_in_date = chicken_in_date
            house.save()
        
        # Generate Task objects from ProgramTask templates
        for program_task in program_tasks:
            # Calculate day_offset based on ProgramTask.day
            day_offset = program_task.day
            
            # Create Task object
            task, created = Task.objects.get_or_create(
                house=house,
                day_offset=day_offset,
                task_name=program_task.title,
                defaults={
                    'description': program_task.description or program_task.title,
                    'task_type': program_task.task_type or 'daily',
                    'notes': f"From program: {program.name}"
                }
            )
            tasks.append(task)
        
        return tasks
