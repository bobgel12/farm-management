from django.core.management.base import BaseCommand
from django.utils import timezone
from tasks.email_service import TaskEmailService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send daily task reminder emails to farm workers (all farms or specific farm)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Send test emails to verify configuration',
        )
        parser.add_argument(
            '--farm-id',
            type=int,
            help='Send email for specific farm ID (or test email for specific farm)',
        )
        parser.add_argument(
            '--test-email',
            type=str,
            help='Email address to send test email to',
        )
        parser.add_argument(
            '--all-farms',
            action='store_true',
            help='Send emails to all farms (default behavior)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force resend even if email was already sent today',
        )

    def handle(self, *args, **options):
        if options['test']:
            self.send_test_email(options)
        else:
            self.send_daily_emails(options)

    def send_daily_emails(self, options):
        """Send daily task reminder emails"""
        farm_id = options.get('farm_id')
        
        if farm_id:
            self.stdout.write(
                self.style.SUCCESS(f'Starting daily task email process for farm {farm_id}...')
            )
            
            try:
                from farms.models import Farm
                farm = Farm.objects.get(id=farm_id)
                force = options.get('force', False)
                sent_count, message = TaskEmailService.send_farm_task_reminders(farm, force=force)
                
                if sent_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(message)
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(message)
                    )
                    
            except Farm.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Farm with ID {farm_id} not found')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error sending daily task emails for farm {farm_id}: {str(e)}')
                )
                logger.error(f'Error in daily task email command for farm {farm_id}: {str(e)}')
        else:
            self.stdout.write(
                self.style.SUCCESS('Starting daily task email process for all farms...')
            )
            
            try:
                sent_count = TaskEmailService.send_daily_task_reminders()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully sent {sent_count} daily task reminder emails'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error sending daily task emails: {str(e)}')
                )
                logger.error(f'Error in daily task email command: {str(e)}')

    def send_test_email(self, options):
        """Send test email"""
        farm_id = options.get('farm_id')
        test_email = options.get('test_email')
        
        if not farm_id:
            self.stdout.write(
                self.style.ERROR('--farm-id is required for test emails')
            )
            return
            
        if not test_email:
            self.stdout.write(
                self.style.ERROR('--test-email is required for test emails')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Sending test email to {test_email} for farm {farm_id}...')
        )
        
        try:
            success, message = TaskEmailService.send_test_email(farm_id, test_email)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'Test email sent successfully: {message}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to send test email: {message}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error sending test email: {str(e)}')
            )
