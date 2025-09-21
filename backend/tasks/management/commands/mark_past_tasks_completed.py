"""
Management command to mark past tasks as completed for all houses
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from tasks.models import Task
from houses.models import House


class Command(BaseCommand):
    help = 'Mark all past tasks as completed for all houses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--house-id',
            type=int,
            help='Only process tasks for a specific house ID',
        )
        parser.add_argument(
            '--farm-id',
            type=int,
            help='Only process tasks for houses in a specific farm ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        house_id = options.get('house_id')
        farm_id = options.get('farm_id')

        # Get houses to process
        houses_query = House.objects.filter(is_active=True)
        
        if house_id:
            houses_query = houses_query.filter(id=house_id)
        elif farm_id:
            houses_query = houses_query.filter(farm_id=farm_id)

        houses = houses_query.all()
        
        if not houses.exists():
            self.stdout.write(
                self.style.WARNING('No active houses found matching the criteria.')
            )
            return

        total_tasks_updated = 0
        total_houses_processed = 0

        for house in houses:
            current_day = house.current_day
            if current_day is None:
                self.stdout.write(
                    self.style.WARNING(f'Skipping house {house.id} - no current day calculated')
                )
                continue

            # Find past tasks (day_offset < current_day) that are not completed
            past_tasks = Task.objects.filter(
                house=house,
                day_offset__lt=current_day,
                is_completed=False
            )

            if not past_tasks.exists():
                self.stdout.write(
                    self.style.SUCCESS(f'House {house} (Day {current_day}): No past tasks to complete')
                )
                continue

            task_count = past_tasks.count()
            total_tasks_updated += task_count
            total_houses_processed += 1

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'[DRY RUN] House {house} (Day {current_day}): Would mark {task_count} past tasks as completed'
                    )
                )
                # Show details of tasks that would be updated
                for task in past_tasks[:5]:  # Show first 5 tasks
                    self.stdout.write(f'  - Day {task.day_offset}: {task.task_name}')
                if task_count > 5:
                    self.stdout.write(f'  ... and {task_count - 5} more tasks')
            else:
                # Mark tasks as completed
                updated_count = past_tasks.update(
                    is_completed=True,
                    completed_at=timezone.now(),
                    completed_by='system_auto_complete',
                    notes='Automatically marked as completed - past task'
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'House {house} (Day {current_day}): Marked {updated_count} past tasks as completed'
                    )
                )

        # Summary
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY RUN SUMMARY] Would update {total_tasks_updated} tasks across {total_houses_processed} houses'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSUMMARY: Updated {total_tasks_updated} tasks across {total_houses_processed} houses'
                )
            )
