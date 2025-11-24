import logging
from typing import List, Dict, Any, Optional, Tuple
from django.db import transaction
from django.utils import timezone
from .models import Program, ProgramTask, Farm, ProgramChangeLog
from houses.models import House
from tasks.models import Task

logger = logging.getLogger(__name__)


class ProgramChangeService:
    """Service to handle program changes and their impact on farms"""
    
    @staticmethod
    def detect_program_changes(program: Program, old_tasks: List[ProgramTask], new_tasks: List[ProgramTask]) -> List[Dict[str, Any]]:
        """Detect changes between old and new program tasks"""
        changes = []
        
        # Create lookup dictionaries
        old_tasks_dict = {task.id: task for task in old_tasks if task.id}
        new_tasks_dict = {task.id: task for task in new_tasks if task.id}
        
        # Find added tasks
        for task in new_tasks:
            if not task.id or task.id not in old_tasks_dict:
                changes.append({
                    'type': 'task_added',
                    'task': task,
                    'description': f"Added task: {task.title} (Day {task.day})"
                })
        
        # Find modified tasks
        for task in new_tasks:
            if task.id and task.id in old_tasks_dict:
                old_task = old_tasks_dict[task.id]
                if ProgramChangeService._task_changed(old_task, task):
                    changes.append({
                        'type': 'task_modified',
                        'task': task,
                        'old_task': old_task,
                        'description': f"Modified task: {task.title} (Day {task.day})"
                    })
        
        # Find deleted tasks
        for task_id, old_task in old_tasks_dict.items():
            if task_id not in new_tasks_dict:
                changes.append({
                    'type': 'task_deleted',
                    'task': old_task,
                    'description': f"Deleted task: {old_task.title} (Day {old_task.day})"
                })
        
        return changes
    
    @staticmethod
    def _task_changed(old_task: ProgramTask, new_task: ProgramTask) -> bool:
        """Check if a task has been modified"""
        fields_to_check = [
            'day', 'task_type', 'title', 'description', 'instructions',
            'priority', 'estimated_duration', 'is_required', 'requires_confirmation',
            'recurring_days'
        ]
        
        for field in fields_to_check:
            old_value = getattr(old_task, field)
            new_value = getattr(new_task, field)
            if old_value != new_value:
                return True
        return False
    
    @staticmethod
    def get_affected_farms(program: Program) -> List[Farm]:
        """Get all farms currently using this program"""
        return list(program.farms.filter(is_active=True))
    
    @staticmethod
    def get_farm_impact_analysis(program: Program, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the impact of program changes on farms"""
        affected_farms = ProgramChangeService.get_affected_farms(program)
        
        analysis = {
            'program': program,
            'affected_farms': affected_farms,
            'changes': changes,
            'impact_summary': {
                'total_farms': len(affected_farms),
                'active_houses': 0,
                'total_tasks_affected': 0,
                'critical_changes': 0,
                'moderate_changes': 0,
                'minor_changes': 0
            }
        }
        
        # Analyze each farm's impact
        for farm in affected_farms:
            farm_houses = farm.houses.filter(is_active=True)
            analysis['impact_summary']['active_houses'] += farm_houses.count()
            
            # Count existing tasks that might be affected
            for house in farm_houses:
                existing_tasks = Task.objects.filter(house=house).count()
                analysis['impact_summary']['total_tasks_affected'] += existing_tasks
        
        # Categorize changes by severity
        for change in changes:
            if change['type'] == 'task_deleted':
                analysis['impact_summary']['critical_changes'] += 1
            elif change['type'] == 'task_modified':
                analysis['impact_summary']['moderate_changes'] += 1
            else:
                analysis['impact_summary']['minor_changes'] += 1
        
        return analysis
    
    @staticmethod
    def create_change_log(program: Program, changes: List[Dict[str, Any]], user_choice: str = None) -> ProgramChangeLog:
        """Create a change log entry for program modifications"""
        affected_farms = ProgramChangeService.get_affected_farms(program)
        
        # Determine the primary change type
        change_types = [change['type'] for change in changes]
        primary_change_type = 'program_modified'
        if 'task_deleted' in change_types:
            primary_change_type = 'task_deleted'
        elif 'task_modified' in change_types:
            primary_change_type = 'task_modified'
        elif 'task_added' in change_types:
            primary_change_type = 'task_added'
        
        change_description = f"Program '{program.name}' modified with {len(changes)} changes"
        
        change_log = ProgramChangeLog.objects.create(
            program=program,
            change_type=primary_change_type,
            change_description=change_description,
            old_data={'changes': [change.get('old_task', {}).__dict__ if 'old_task' in change else {} for change in changes]},
            new_data={'changes': [change.get('task', {}).__dict__ for change in changes]},
            user_choice=user_choice
        )
        
        change_log.affected_farms.set(affected_farms)
        return change_log
    
    @staticmethod
    def apply_retroactive_changes(change_log: ProgramChangeLog) -> bool:
        """Apply program changes retroactively to existing farm tasks"""
        try:
            with transaction.atomic():
                affected_farms = change_log.affected_farms.all()
                
                for farm in affected_farms:
                    # Get all active houses for this farm
                    houses = farm.houses.filter(is_active=True)
                    
                    for house in houses:
                        # Apply changes to existing tasks
                        ProgramChangeService._apply_changes_to_house(house, change_log)
                
                # Mark as processed
                change_log.processed_at = timezone.now()
                change_log.save()
                
                logger.info(f"Successfully applied retroactive changes for program {change_log.program.name}")
                return True
                
        except Exception as e:
            logger.error(f"Error applying retroactive changes: {str(e)}")
            return False
    
    @staticmethod
    def _apply_changes_to_house(house: House, change_log: ProgramChangeLog):
        """Apply program changes to a specific house's tasks"""
        changes = change_log.new_data.get('changes', [])
        
        for change_data in changes:
            if not change_data:
                continue
                
            task_type = change_data.get('type', '')
            
            if task_type == 'task_added':
                # Create new task for this house
                ProgramChangeService._create_task_from_program_task(house, change_data)
            elif task_type == 'task_modified':
                # Update existing task
                ProgramChangeService._update_task_from_program_task(house, change_data)
            elif task_type == 'task_deleted':
                # Mark existing tasks as inactive or delete them
                ProgramChangeService._remove_task_from_program_task(house, change_data)
    
    @staticmethod
    def _create_task_from_program_task(house: House, program_task_data: Dict[str, Any]):
        """Create a new task for a house based on program task data"""
        from tasks.models import Task
        
        Task.objects.create(
            house=house,
            title=program_task_data.get('title', ''),
            description=program_task_data.get('description', ''),
            due_date=house.chicken_in_date + timezone.timedelta(days=program_task_data.get('day', 0)) if house.chicken_in_date else None,
            priority=program_task_data.get('priority', 'medium'),
            is_completed=False,
            task_type=program_task_data.get('task_type', 'daily'),
            estimated_duration=program_task_data.get('estimated_duration', 30),
            is_required=program_task_data.get('is_required', True),
            requires_confirmation=program_task_data.get('requires_confirmation', False)
        )
    
    @staticmethod
    def _update_task_from_program_task(house: House, program_task_data: Dict[str, Any]):
        """Update existing task based on program task changes"""
        from tasks.models import Task
        
        # Find matching task by title and day
        tasks = Task.objects.filter(
            house=house,
            title=program_task_data.get('title', '')
        )
        
        for task in tasks:
            task.description = program_task_data.get('description', task.description)
            task.priority = program_task_data.get('priority', task.priority)
            task.task_type = program_task_data.get('task_type', task.task_type)
            task.estimated_duration = program_task_data.get('estimated_duration', task.estimated_duration)
            task.is_required = program_task_data.get('is_required', task.is_required)
            task.requires_confirmation = program_task_data.get('requires_confirmation', task.requires_confirmation)
            task.save()
    
    @staticmethod
    def _remove_task_from_program_task(house: House, program_task_data: Dict[str, Any]):
        """Remove or deactivate task based on program task deletion"""
        from tasks.models import Task
        
        # Find matching tasks and mark as inactive
        tasks = Task.objects.filter(
            house=house,
            title=program_task_data.get('title', '')
        )
        
        for task in tasks:
            task.is_active = False
            task.save()
    
    @staticmethod
    def get_pending_changes() -> List[ProgramChangeLog]:
        """Get all pending program changes that need user decision"""
        return ProgramChangeLog.objects.filter(
            user_choice__isnull=True,
            processed_at__isnull=True
        ).order_by('-created_at')

    @staticmethod
    def regenerate_tasks_for_farm(farm: Farm, force_regenerate: bool = True) -> bool:
        """Regenerate tasks for all active houses in a farm when program changes"""
        try:
            from tasks.task_scheduler import TaskScheduler
            from houses.models import House
            
            if not farm.program:
                logger.warning(f"Cannot regenerate tasks for farm {farm.name}: no program assigned")
                return False
            
            houses = farm.houses.filter(is_active=True)
            total_tasks_regenerated = 0
            
            for house in houses:
                try:
                    # Regenerate tasks for this house
                    tasks = TaskScheduler.generate_tasks_from_program(
                        house, 
                        farm.program, 
                        force_regenerate=force_regenerate
                    )
                    total_tasks_regenerated += len(tasks)
                    logger.info(f"Regenerated {len(tasks)} tasks for house {house.house_number} in farm {farm.name}")
                except Exception as e:
                    logger.error(f"Error regenerating tasks for house {house.house_number}: {str(e)}")
                    continue
            
            logger.info(f"Successfully regenerated tasks for {houses.count()} houses in farm {farm.name} (total: {total_tasks_regenerated} tasks)")
            return True
            
        except Exception as e:
            logger.error(f"Error regenerating tasks for farm {farm.name}: {str(e)}")
            return False