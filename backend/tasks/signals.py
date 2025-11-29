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
    or when a house's chicken_in_date or current_age_days is updated
    """
    # Use age_days which prefers current_age_days (from Rotem) over calculated current_day
    age_days = instance.age_days
    if age_days is not None and age_days > 0:
        # Mark past tasks as completed
        past_tasks = Task.objects.filter(
            house=instance,
            day_offset__lt=age_days,
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
        # Use age_days which prefers current_age_days (from Rotem) over calculated current_day
        age_days = house.age_days
        if age_days is not None and age_days > 0:
            # Mark past tasks as completed
            past_tasks = Task.objects.filter(
                house=house,
                day_offset__lt=age_days,
                is_completed=False
            )
            
            if past_tasks.exists():
                past_tasks.update(
                    is_completed=True,
                    completed_at=timezone.now(),
                    completed_by='system_auto_complete',
                    notes='Automatically marked as completed - past task after farm update'
                )
