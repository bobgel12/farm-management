from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import EmailTask, Task
from farms.models import Farm, Worker
from houses.models import House
import logging

logger = logging.getLogger(__name__)


class TaskEmailService:
    """Service for sending daily task reminder emails"""
    
    @staticmethod
    def send_daily_task_reminders():
        """Send daily task reminders to all active farms with workers"""
        farms = Farm.objects.filter(is_active=True)
        sent_count = 0
        
        for farm in farms:
            try:
                # Check if email was already sent today
                if EmailTask.objects.filter(farm=farm, sent_date=timezone.now().date()).exists():
                    logger.info(f"Email already sent today for farm {farm.name}")
                    continue
                
                # Get active workers who want to receive daily tasks
                workers = farm.workers.filter(
                    is_active=True, 
                    receive_daily_tasks=True
                )
                
                if not workers.exists():
                    logger.info(f"No active workers found for farm {farm.name}")
                    continue
                
                # Get today's and tomorrow's tasks for all active houses
                task_data = TaskEmailService._get_farm_task_data(farm)
                
                if not task_data['houses']:
                    logger.info(f"No active houses with tasks found for farm {farm.name}")
                    continue
                
                # Send email to all workers
                success = TaskEmailService._send_farm_task_email(farm, workers, task_data)
                
                if success:
                    sent_count += 1
                    logger.info(f"Successfully sent task email for farm {farm.name}")
                else:
                    logger.error(f"Failed to send task email for farm {farm.name}")
                    
            except Exception as e:
                logger.error(f"Error sending task email for farm {farm.name}: {str(e)}")
        
        logger.info(f"Daily task reminder process completed. Sent {sent_count} emails.")
        return sent_count
    
    @staticmethod
    def _get_farm_task_data(farm):
        """Get task data for a farm's active houses"""
        today = timezone.now().date()
        houses = House.objects.filter(farm=farm, is_active=True)
        
        task_data = {
            'farm_name': farm.name,
            'date': today,
            'houses': []
        }
        
        for house in houses:
            current_day = house.current_day
            if current_day is None:
                continue
                
            # Get today's tasks
            today_tasks = Task.objects.filter(
                house=house,
                day_offset=current_day,
                is_completed=False
            ).order_by('task_name')
            
            # Get tomorrow's tasks
            tomorrow_tasks = Task.objects.filter(
                house=house,
                day_offset=current_day + 1,
                is_completed=False
            ).order_by('task_name')
            
            # Only include houses that have tasks
            if today_tasks.exists() or tomorrow_tasks.exists():
                house_data = {
                    'id': house.id,
                    'house_number': house.house_number,
                    'current_day': current_day,
                    'status': house.status,
                    'chicken_in_date': house.chicken_in_date,
                    'today_tasks': [
                        {
                            'id': task.id,
                            'name': task.task_name,
                            'description': task.description,
                            'type': task.task_type
                        }
                        for task in today_tasks
                    ],
                    'tomorrow_tasks': [
                        {
                            'id': task.id,
                            'name': task.task_name,
                            'description': task.description,
                            'type': task.task_type
                        }
                        for task in tomorrow_tasks
                    ]
                }
                task_data['houses'].append(house_data)
        
        return task_data
    
    @staticmethod
    def _send_farm_task_email(farm, workers, task_data):
        """Send task reminder email to workers"""
        try:
            # Prepare email data
            recipient_emails = [worker.email for worker in workers]
            recipient_names = [worker.name for worker in workers]
            
            # Calculate total task count
            total_tasks = sum(
                len(house['today_tasks']) + len(house['tomorrow_tasks']) 
                for house in task_data['houses']
            )
            
            # Email subject
            subject = f"Daily Task Reminder - {farm.name} ({task_data['date'].strftime('%B %d, %Y')})"
            
            # Render HTML email template
            html_content = render_to_string('tasks/daily_task_email.html', {
                'farm_name': farm.name,
                'date': task_data['date'],
                'houses': task_data['houses'],
                'total_tasks': total_tasks,
                'recipient_names': recipient_names
            })
            
            # Render plain text email template
            text_content = render_to_string('tasks/daily_task_email.txt', {
                'farm_name': farm.name,
                'date': task_data['date'],
                'houses': task_data['houses'],
                'total_tasks': total_tasks,
                'recipient_names': recipient_names
            })
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_emails
            )
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            
            # Record the sent email
            EmailTask.objects.create(
                farm=farm,
                sent_date=task_data['date'],
                sent_time=timezone.now().time(),
                recipients=recipient_emails,
                subject=subject,
                houses_included=[house['id'] for house in task_data['houses']],
                tasks_count=total_tasks
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {recipient_emails}: {str(e)}")
            return False
    
    @staticmethod
    def send_test_email(farm_id, test_email):
        """Send a test email to verify email configuration"""
        try:
            farm = Farm.objects.get(id=farm_id)
            workers = farm.workers.filter(is_active=True, receive_daily_tasks=True)
            
            if not workers.exists():
                return False, "No active workers found for this farm"
            
            task_data = TaskEmailService._get_farm_task_data(farm)
            
            if not task_data['houses']:
                return False, "No active houses with tasks found for this farm"
            
            # Send test email to specified address
            test_workers = [type('Worker', (), {'email': test_email, 'name': 'Test User'})()]
            success = TaskEmailService._send_farm_task_email(farm, test_workers, task_data)
            
            return success, "Test email sent successfully" if success else "Failed to send test email"
            
        except Farm.DoesNotExist:
            return False, "Farm not found"
        except Exception as e:
            return False, f"Error: {str(e)}"
