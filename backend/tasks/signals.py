"""
Signal handlers for task management
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from tasks.models import Task
from houses.models import House
from farms.models import Farm


@receiver(post_save, sender=House)
def auto_complete_past_tasks_for_house(sender, instance, created, **kwargs):
    """
    Automatically mark past tasks as completed when a new house is created
    or when a house's chicken_in_date is updated
    """
    # Check if chicken_in_date exists and current_day > 0
    if instance.chicken_in_date:
        current_day = instance.current_day
        if current_day is not None and current_day > 0:
            # Mark past tasks as completed
            past_tasks = Task.objects.filter(
                house=instance,
                day_offset__lt=current_day,
                is_completed=False
            )
            
            if past_tasks.exists():
                action = 'creation' if created else 'update'
                past_tasks.update(
                    is_completed=True,
                    completed_at=timezone.now(),
                    completed_by='system_auto_complete',
                    notes=f'Automatically marked as completed - past task after house {action}'
                )


@receiver(post_save, sender=Farm)
def auto_complete_past_tasks_for_farm(sender, instance, created, **kwargs):
    """
    Automatically mark past tasks as completed for all houses in a farm
    when a new farm is created (though this is less likely to have past tasks)
    """
    if created:
        # New farm created - no houses yet, so no tasks to complete
        return
    
    # If farm was updated, check all its houses for past tasks
    houses = instance.houses.filter(is_active=True)
    
    for house in houses:
        current_day = house.current_day
        if current_day is not None and current_day > 0:
            # Mark past tasks as completed
            past_tasks = Task.objects.filter(
                house=house,
                day_offset__lt=current_day,
                is_completed=False
            )
            
            if past_tasks.exists():
                past_tasks.update(
                    is_completed=True,
                    completed_at=timezone.now(),
                    completed_by='system_auto_complete',
                    notes='Automatically marked as completed - past task after farm update'
                )
