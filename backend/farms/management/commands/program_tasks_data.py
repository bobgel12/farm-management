"""
Sample program tasks data for seeding
"""
from datetime import datetime, timedelta

def get_standard_program_tasks():
    """Get tasks for the standard 40-day program"""
    return [
        # Setup day (-1)
        {
            'day': -1, 'task_type': 'one_time', 'title': 'House Setup - Heater Preparation',
            'description': 'Open heater pipe lock, turn heater 24 hours ahead',
            'instructions': '1. Check heat line is down\n2. Turn on heater\n3. Verify temperature reaches target',
            'priority': 'critical', 'estimated_duration': 60, 'is_required': True
        },
        {
            'day': -1, 'task_type': 'one_time', 'title': 'Water System Setup',
            'description': 'Set up water system and check water line',
            'instructions': '1. Turn on water\n2. Check water line\n3. Replace filter\n4. Set water pressure to 6 half turns',
            'priority': 'high', 'estimated_duration': 45, 'is_required': True
        },
        {
            'day': -1, 'task_type': 'one_time', 'title': 'Feed System Setup',
            'description': 'Set up feeding system and prepare feed trays',
            'instructions': '1. Set water line height to 6 full turns\n2. Place 16 plastic trays (5 loads each)\n3. Set up turbo\n4. Lock mid house feed line\n5. Run feed line to full',
            'priority': 'high', 'estimated_duration': 90, 'is_required': True
        },
        
        # Day 0 - Chicken arrival
        {
            'day': 0, 'task_type': 'one_time', 'title': 'Chicken Arrival - Initial Check',
            'description': 'Chickens arrive, perform initial checks',
            'instructions': '1. Check water line has water to the end\n2. Verify heater is running\n3. Ensure feed is full\n4. Monitor chick behavior',
            'priority': 'critical', 'estimated_duration': 120, 'is_required': True
        },
        
        # Day 1
        {
            'day': 1, 'task_type': 'one_time', 'title': 'Increase Water Pressure',
            'description': 'Increase water pressure by 1 half turn',
            'instructions': '1. Check current pressure\n2. Increase by 1 half turn\n3. Verify water flow',
            'priority': 'medium', 'estimated_duration': 15, 'is_required': True
        },
        
        # Days 1-7: Daily tasks
        {
            'day': 1, 'task_type': 'daily', 'title': 'Death Chicken Pickup',
            'description': 'Pick up dead chickens every 2 days',
            'instructions': '1. Walk through house\n2. Identify dead chickens\n3. Remove carefully\n4. Record count',
            'priority': 'high', 'estimated_duration': 30, 'is_required': True
        },
        {
            'day': 1, 'task_type': 'daily', 'title': 'Manual Feed Setup',
            'description': 'Turn on feed manually twice daily',
            'instructions': '1. Morning: Turn on feed system\n2. Afternoon: Turn on feed system\n3. Check feed levels',
            'priority': 'high', 'estimated_duration': 20, 'is_required': True
        },
        
        # Day 7
        {
            'day': 7, 'task_type': 'one_time', 'title': 'Close Turbo Feed',
            'description': 'Close turbo feed and push out',
            'instructions': '1. Close turbo feed system\n2. Push out remaining feed\n3. Clean turbo area',
            'priority': 'medium', 'estimated_duration': 30, 'is_required': True
        },
        {
            'day': 7, 'task_type': 'one_time', 'title': 'Close Curtains',
            'description': 'Close front and back curtains',
            'instructions': '1. Close front curtain\n2. Close back curtain\n3. Check for gaps',
            'priority': 'medium', 'estimated_duration': 20, 'is_required': True
        },
        
        # Day 8
        {
            'day': 8, 'task_type': 'one_time', 'title': 'Full House Operations',
            'description': 'Set up full house operations',
            'instructions': '1. Increase water pressure by 1 half turn\n2. Turn on feed and water to full house\n3. Turn feed to 3/4 front and back\n4. Turn on heat 1, 2, 7, 8\n5. Open separators\n6. Turn feed on automatic',
            'priority': 'critical', 'estimated_duration': 120, 'is_required': True
        },
        
        # Days 9-12
        {
            'day': 9, 'task_type': 'daily', 'title': 'Check Feeder Motor',
            'description': 'Check feeder motor on last pan twice daily',
            'instructions': '1. Early morning: Check motor\n2. End of day: Check motor\n3. Clean out to ensure feed runs\n4. Run line 2 times',
            'priority': 'medium', 'estimated_duration': 30, 'is_required': True
        },
        {
            'day': 9, 'task_type': 'one_time', 'title': 'Check Chicken Spread',
            'description': 'Check if chickens spread out evenly',
            'instructions': '1. Observe chicken distribution\n2. If uneven, adjust separators\n3. Close separators on day 10 if even',
            'priority': 'medium', 'estimated_duration': 20, 'is_required': True
        },
        {
            'day': 12, 'task_type': 'one_time', 'title': 'Clean Up Turbo Line',
            'description': 'Clean up turbo line to ceiling',
            'instructions': '1. Remove turbo line\n2. Clean thoroughly\n3. Store at ceiling level',
            'priority': 'low', 'estimated_duration': 45, 'is_required': True
        },
        
        # Day 13
        {
            'day': 13, 'task_type': 'one_time', 'title': 'Raise Feeder Line',
            'description': 'Raise feeder line so pan doesn\'t touch ground',
            'instructions': '1. Check current height\n2. Raise feeder line\n3. Level the feeder line\n4. Ensure pans don\'t touch ground',
            'priority': 'medium', 'estimated_duration': 60, 'is_required': True
        },
        
        # Day 14
        {
            'day': 14, 'task_type': 'one_time', 'title': 'Increase Water Pressure',
            'description': 'Increase water pressure by 1 half turn',
            'instructions': '1. Check current pressure\n2. Increase by 1 half turn\n3. Verify water flow',
            'priority': 'medium', 'estimated_duration': 15, 'is_required': True
        },
        
        # Day 20
        {
            'day': 20, 'task_type': 'one_time', 'title': 'Turn On Coolpad Water',
            'description': 'Turn water on for coolpad system',
            'instructions': '1. Check coolpad system\n2. Turn on water supply\n3. Verify water flow',
            'priority': 'medium', 'estimated_duration': 30, 'is_required': True
        },
        
        # Day 21
        {
            'day': 21, 'task_type': 'one_time', 'title': 'Activate Coolpad System',
            'description': 'Turn on complete coolpad system',
            'instructions': '1. Turn coolpad breaker\n2. Turn water on coolpad\n3. Turn controller coolpad on auto\n4. Monitor temperature',
            'priority': 'high', 'estimated_duration': 45, 'is_required': True
        },
        
        # Days 35-40: Chicken out preparation
        {
            'day': 35, 'task_type': 'one_time', 'title': 'Schedule Chicken Out',
            'description': 'Keep asking for chicken out schedule',
            'instructions': '1. Confirm date and time\n2. Plan logistics\n3. Prepare equipment',
            'priority': 'high', 'estimated_duration': 30, 'is_required': True
        },
        {
            'day': 39, 'task_type': 'one_time', 'title': 'Pre-Out Preparation',
            'description': 'One day before chicken out - increase water pressure',
            'instructions': '1. Turn water pressure 2 half circles\n2. Prepare for next day',
            'priority': 'high', 'estimated_duration': 20, 'is_required': True
        },
        {
            'day': 40, 'task_type': 'one_time', 'title': 'Chicken Out Day',
            'description': 'Complete chicken out process',
            'instructions': '1. 12h before: Turn off feeder\n2. 10h before: Clean auger and feeder line\n3. 6h before: Raise feeder line\n4. Turn off heater and raise up\n5. 1h before: Turn off water line and raise up\n6. Turn on front water line\n7. Turn off tunnel fan and light\n8. 3h after: Complete cleanup',
            'priority': 'critical', 'estimated_duration': 480, 'is_required': True
        },
        {
            'day': 41, 'task_type': 'one_time', 'title': 'Post-Out Cleanup',
            'description': 'One day after chicken out - final cleanup',
            'instructions': '1. Collect remaining dead chickens\n2. Final house cleanup\n3. Prepare for next batch',
            'priority': 'medium', 'estimated_duration': 120, 'is_required': True
        },
        
        # Recurring tasks
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

def get_extended_program_tasks():
    """Get tasks for the extended 45-day program"""
    tasks = get_standard_program_tasks()
    
    # Add additional tasks for days 41-45
    additional_tasks = [
        {
            'day': 42, 'task_type': 'daily', 'title': 'Extended Growth Monitoring',
            'description': 'Monitor chicken growth and health during extended period',
            'instructions': '1. Check weight gain\n2. Monitor health\n3. Adjust feed if needed',
            'priority': 'medium', 'estimated_duration': 45, 'is_required': True
        },
        {
            'day': 45, 'task_type': 'one_time', 'title': 'Extended Program Out',
            'description': 'Chicken out for extended program',
            'instructions': 'Follow standard out process but for day 45',
            'priority': 'critical', 'estimated_duration': 480, 'is_required': True
        }
    ]
    
    return tasks + additional_tasks

def get_quick_program_tasks():
    """Get tasks for the quick 35-day program"""
    tasks = get_standard_program_tasks()
    
    # Modify some tasks for quicker timeline
    # Remove extended tasks and adjust timing
    filtered_tasks = []
    for task in tasks:
        if task['day'] <= 35:  # Only include tasks up to day 35
            filtered_tasks.append(task)
    
    # Add quick program specific tasks
    quick_tasks = [
        {
            'day': 35, 'task_type': 'one_time', 'title': 'Quick Program Out',
            'description': 'Chicken out for quick program',
            'instructions': 'Follow standard out process but for day 35',
            'priority': 'critical', 'estimated_duration': 480, 'is_required': True
        }
    ]
    
    return filtered_tasks + quick_tasks
