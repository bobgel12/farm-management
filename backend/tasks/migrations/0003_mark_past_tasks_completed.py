# Generated manually for marking past tasks as completed

from django.db import migrations
from django.utils import timezone


def mark_past_tasks_completed(apps, schema_editor):
    """
    Mark all past tasks as completed for all houses
    """
    Task = apps.get_model('tasks', 'Task')
    House = apps.get_model('houses', 'House')
    
    # Get all active houses
    houses = House.objects.filter(is_active=True)
    
    for house in houses:
        # Calculate current day for the house
        if not house.chicken_in_date:
            continue
            
        today = timezone.now().date()
        if house.chicken_out_date and today > house.chicken_out_date:
            continue  # House is empty
            
        current_day = (today - house.chicken_in_date).days
        
        if current_day > 0:
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
                    completed_by='migration_auto_complete',
                    notes='Automatically marked as completed by migration - past task'
                )


def reverse_mark_past_tasks_completed(apps, schema_editor):
    """
    Reverse migration - mark tasks as incomplete if they were completed by migration
    """
    Task = apps.get_model('tasks', 'Task')
    
    # Mark tasks completed by migration as incomplete
    Task.objects.filter(
        completed_by='migration_auto_complete',
        notes='Automatically marked as completed by migration - past task'
    ).update(
        is_completed=False,
        completed_at=None,
        completed_by='',
        notes=''
    )


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_alter_recurringtask_options_alter_task_options_and_more'),
        ('houses', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            mark_past_tasks_completed,
            reverse_mark_past_tasks_completed,
        ),
    ]
