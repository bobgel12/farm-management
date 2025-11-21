from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import EmailTask, Task
from farms.models import Farm, Worker
from houses.models import House
from .email_alternatives import EmailService
import logging
import os

logger = logging.getLogger(__name__)


class TaskEmailService:
    """Service for sending daily task reminder emails"""
    
    @staticmethod
    def send_daily_task_reminders(force=False):
        """Send daily task reminders to all active farms with workers"""
        # Check if email is disabled due to Railway restrictions
        if os.getenv('DISABLE_EMAIL', 'False').lower() == 'true':
            logger.info("Email sending is disabled due to Railway network restrictions")
            return 0
            
        farms = Farm.objects.filter(is_active=True)
        sent_count = 0
        
        for farm in farms:
            try:
                # Check if email was already sent today (unless force is True)
                if not force and EmailTask.objects.filter(farm=farm, sent_date=timezone.now().date()).exists():
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
    def send_farm_task_reminders(farm, force=False):
        """Send daily task reminders for a specific farm
        
        Returns:
            tuple: (sent_count, message) where sent_count is 0 or 1, and message explains the result
        """
        try:
            # Check if email was already sent today (unless force is True)
            if not force and EmailTask.objects.filter(farm=farm, sent_date=timezone.now().date()).exists():
                logger.info(f"Email already sent today for farm {farm.name}")
                return 0, f"Email already sent today for {farm.name}. Use force=True to resend."
            
            # Get active workers who want to receive daily tasks
            workers = farm.workers.filter(
                is_active=True, 
                receive_daily_tasks=True
            )
            
            if not workers.exists():
                logger.info(f"No active workers found for farm {farm.name}")
                return 0, f"No active workers with receive_daily_tasks=True found for {farm.name}"
            
            # Get today's and tomorrow's tasks for all active houses
            task_data = TaskEmailService._get_farm_task_data(farm)
            
            if not task_data['houses']:
                logger.info(f"No active houses with tasks found for farm {farm.name}")
                return 0, f"No active houses with tasks found for {farm.name}"
            
            # Send email to all workers
            success = TaskEmailService._send_farm_task_email(farm, workers, task_data)
            
            if success:
                logger.info(f"Successfully sent task email for farm {farm.name}")
                return 1, f"Successfully sent daily task reminder email for {farm.name}"
            else:
                logger.error(f"Failed to send task email for farm {farm.name}")
                return 0, f"Failed to send email for {farm.name}. Check email configuration and logs."
                
        except Exception as e:
            logger.error(f"Error sending task email for farm {farm.name}: {str(e)}")
            return 0, f"Error sending email for {farm.name}: {str(e)}"
    
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
            
            # If no tasks for today/tomorrow, get upcoming tasks (next 7 days)
            if not today_tasks.exists() and not tomorrow_tasks.exists():
                upcoming_tasks = Task.objects.filter(
                    house=house,
                    day_offset__gte=current_day,
                    day_offset__lte=current_day + 7,
                    is_completed=False
                ).order_by('day_offset', 'task_name')[:10]  # Limit to 10 upcoming tasks
                
                if upcoming_tasks.exists():
                    # Group by day_offset
                    today_tasks_list = []
                    tomorrow_tasks_list = []
                    for task in upcoming_tasks:
                        if task.day_offset == current_day:
                            today_tasks_list.append(task)
                        elif task.day_offset == current_day + 1:
                            tomorrow_tasks_list.append(task)
                        elif not today_tasks_list:  # If no today tasks, use first upcoming
                            today_tasks_list.append(task)
                    
                    today_tasks = today_tasks_list
                    tomorrow_tasks = tomorrow_tasks_list
            
            # Only include houses that have tasks
            if today_tasks or tomorrow_tasks:
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
            
            # Use SendGrid API instead of SMTP for Railway
            if os.getenv('EMAIL_HOST', '').endswith('sendgrid.net'):
                return TaskEmailService._send_via_sendgrid_api(recipient_emails, subject, text_content, html_content)
            else:
                # Send email with timeout for other providers
                import socket
                import smtplib
                
                # Set timeout for SMTP connection
                socket.setdefaulttimeout(10)  # 10 second timeout
                
                try:
                    email.send()
                except (socket.timeout, smtplib.SMTPException, OSError) as e:
                    logger.error(f"SMTP connection failed: {str(e)}")
                    # Return False to indicate failure
                    return False
            
            # Record the sent email (update if exists, create if not)
            EmailTask.objects.update_or_create(
                farm=farm,
                sent_date=task_data['date'],
                defaults={
                    'sent_time': timezone.now().time(),
                    'recipients': recipient_emails,
                    'subject': subject,
                    'houses_included': [house['id'] for house in task_data['houses']],
                    'tasks_count': total_tasks
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {recipient_emails}: {str(e)}")
            return False
    
    @staticmethod
    def _send_via_sendgrid_api(recipients, subject, text_content, html_content):
        """Send email via SendGrid Python Library"""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            api_key = os.getenv('EMAIL_HOST_PASSWORD')  # SendGrid API key
            from_email = settings.DEFAULT_FROM_EMAIL
            
            # Validate API key
            if not api_key or not api_key.startswith('SG.'):
                logger.error("Invalid SendGrid API key format")
                return False
            
            logger.info(f"Sending SendGrid email to {len(recipients)} recipients")
            logger.info(f"From: {from_email}, Subject: {subject}")
            
            # Create SendGrid client
            sg = SendGridAPIClient(api_key=api_key)
            
            # Create Mail object
            message = Mail(
                from_email=from_email,
                to_emails=recipients,
                subject=subject,
                html_content=html_content if html_content else None,
                plain_text_content=text_content
            )
            
            # Send email
            response = sg.send(message)
            
            # Log response details for debugging
            logger.info(f"SendGrid response status: {response.status_code}")
            logger.info(f"SendGrid response headers: {response.headers}")
            
            if response.status_code in [200, 202]:
                logger.info(f"SendGrid email sent successfully to {recipients}")
                return True
            else:
                logger.error(f"SendGrid API error: Status {response.status_code}")
                logger.error(f"SendGrid response body: {response.body}")
                return False
            
        except Exception as e:
            logger.error(f"SendGrid email failed: {str(e)}")
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
            
            # Send test email directly without creating EmailTask record
            success = TaskEmailService._send_test_email_direct(farm, test_email, task_data)
            
            return success, "Test email sent successfully" if success else "Failed to send test email"
            
        except Farm.DoesNotExist:
            return False, "Farm not found"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def _send_test_email_direct(farm, test_email, task_data):
        """Send test email directly without creating EmailTask record"""
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            from django.utils import timezone
            
            # Prepare email content
            subject = f"Test Email - Daily Tasks for {farm.name}"
            
            # Create simple text content
            tomorrow_date = task_data['date'] + timezone.timedelta(days=1)
            text_content = f"""
Test Email - Daily Tasks for {farm.name}

Today's Tasks ({task_data['date']}):
{chr(10).join([f"- House {house['house_number']}: {len(house['today_tasks'])} tasks" for house in task_data['houses']])}

Tomorrow's Tasks ({tomorrow_date}):
{chr(10).join([f"- House {house['house_number']}: {len(house['tomorrow_tasks'])} tasks" for house in task_data['houses']])}

This is a test email to verify email configuration.
"""
            
            # Log email configuration for debugging
            logger.info(f"Email configuration - Host: {settings.EMAIL_HOST}")
            logger.info(f"Email configuration - Port: {settings.EMAIL_PORT}")
            logger.info(f"Email configuration - User: {settings.EMAIL_HOST_USER}")
            logger.info(f"Email configuration - Password: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'Not set'}")
            logger.info(f"Email configuration - From: {settings.DEFAULT_FROM_EMAIL}")
            logger.info(f"Email configuration - Backend: {settings.EMAIL_BACKEND}")
            
            # Use SendGrid API for test emails on Railway
            if os.getenv('EMAIL_HOST', '').endswith('sendgrid.net'):
                return TaskEmailService._send_via_sendgrid_api([test_email], subject, text_content, None)
            else:
                # Send simple email with timeout for other providers
                import socket
                import smtplib
                
                # Set timeout for SMTP connection
                socket.setdefaulttimeout(10)  # 10 second timeout
                
                try:
                    send_mail(
                        subject=subject,
                        message=text_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[test_email],
                        fail_silently=False
                    )
                except (socket.timeout, smtplib.SMTPException, OSError) as e:
                    logger.error(f"SMTP connection failed: {str(e)}")
                    logger.error("Email sending failed - check SMTP configuration and network connectivity")
                    return False
            
            logger.info(f"Test email sent successfully to {test_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending test email to {test_email}: {str(e)}")
            return False
