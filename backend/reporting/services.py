"""
Services for report generation and management
"""
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class ReportGenerationService:
    """Service for generating reports"""
    
    @staticmethod
    def generate_report_from_template(template, parameters=None, export_format='pdf'):
        """
        Generate a report from a template
        
        Args:
            template: ReportTemplate instance
            parameters: Report parameters (filters, date range, etc.)
            export_format: Export format (pdf, excel, csv, json, html)
        
        Returns:
            ReportExecution instance
        """
        from reporting.models import ReportExecution
        
        if parameters is None:
            parameters = {}
        
        # Create report execution record
        execution = ReportExecution.objects.create(
            template=template,
            parameters=parameters,
            export_format=export_format,
            status='pending',
            organization=template.organization,
            started_at=timezone.now()
        )
        
        try:
            execution.status = 'processing'
            execution.save()
            
            # Generate report based on template type
            report_data = ReportGenerationService._generate_report_data(template, parameters)
            
            # Generate file based on export format
            file_path = ReportGenerationService._generate_report_file(
                template, report_data, export_format
            )
            
            if file_path:
                execution.report_file = file_path
                execution.status = 'completed'
            else:
                execution.status = 'failed'
                execution.error_message = 'Failed to generate report file'
            
            execution.completed_at = timezone.now()
            execution_time = (execution.completed_at - execution.started_at).total_seconds()
            execution.execution_time_seconds = execution_time
            execution.save()
            
            logger.info(f"Generated report {execution.id} in {execution_time:.2f}s")
            
        except Exception as e:
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.completed_at = timezone.now()
            execution.save()
            logger.error(f"Error generating report {execution.id}: {str(e)}")
        
        return execution
    
    @staticmethod
    def _generate_report_data(template, parameters):
        """Generate report data based on template configuration"""
        report_type = template.report_type
        data_source = template.data_source
        template_config = template.template_config
        
        report_data = {
            'type': report_type,
            'generated_at': timezone.now().isoformat(),
            'parameters': parameters,
            'data': {}
        }
        
        # Generate data based on report type
        if report_type == 'flock_performance':
            report_data['data'] = ReportGenerationService._generate_flock_performance_data(
                template.organization, parameters
            )
        
        elif report_type == 'farm_summary':
            report_data['data'] = ReportGenerationService._generate_farm_summary_data(
                template.organization, parameters
            )
        
        elif report_type == 'house_status':
            report_data['data'] = ReportGenerationService._generate_house_status_data(
                template.organization, parameters
            )
        
        elif report_type == 'task_completion':
            report_data['data'] = ReportGenerationService._generate_task_completion_data(
                template.organization, parameters
            )
        
        elif report_type == 'custom':
            # Use custom query from template config
            report_data['data'] = ReportGenerationService._generate_custom_data(
                template, parameters
            )
        
        return report_data
    
    @staticmethod
    def _generate_flock_performance_data(organization, parameters):
        """Generate flock performance report data"""
        from farms.models import Flock
        
        flocks = Flock.objects.filter(
            house__farm__organization=organization
        )
        
        # Apply filters
        if parameters.get('farm_id'):
            flocks = flocks.filter(house__farm_id=parameters['farm_id'])
        
        if parameters.get('breed_id'):
            flocks = flocks.filter(breed_id=parameters['breed_id'])
        
        if parameters.get('status'):
            flocks = flocks.filter(status=parameters['status'])
        
        if parameters.get('date_from'):
            flocks = flocks.filter(arrival_date__gte=parameters['date_from'])
        
        if parameters.get('date_to'):
            flocks = flocks.filter(arrival_date__lte=parameters['date_to'])
        
        flock_data = []
        for flock in flocks:
            flock_data.append({
                'flock_code': flock.flock_code,
                'batch_number': flock.batch_number,
                'house': str(flock.house),
                'farm': flock.house.farm.name,
                'breed': flock.breed.name if flock.breed else None,
                'arrival_date': flock.arrival_date.isoformat(),
                'current_age_days': flock.current_age_days,
                'initial_count': flock.initial_chicken_count,
                'current_count': flock.current_chicken_count,
                'mortality_rate': flock.mortality_rate,
                'livability': flock.livability,
                'status': flock.status
            })
        
        return {
            'flocks': flock_data,
            'total_flocks': len(flock_data)
        }
    
    @staticmethod
    def _generate_farm_summary_data(organization, parameters):
        """Generate farm summary report data"""
        from farms.models import Farm
        
        farms = Farm.objects.filter(
            organization=organization,
            is_active=True
        )
        
        farm_data = []
        for farm in farms:
            farm_data.append({
                'name': farm.name,
                'location': farm.location,
                'total_houses': farm.total_houses,
                'active_houses': farm.active_houses,
                'integration_status': farm.integration_status,
                'created_at': farm.created_at.isoformat()
            })
        
        return {
            'farms': farm_data,
            'total_farms': len(farm_data)
        }
    
    @staticmethod
    def _generate_house_status_data(organization, parameters):
        """Generate house status report data"""
        from houses.models import House
        
        houses = House.objects.filter(
            farm__organization=organization,
            is_active=True
        )
        
        house_data = []
        for house in houses:
            house_data.append({
                'house_number': house.house_number,
                'farm': house.farm.name,
                'capacity': house.capacity,
                'current_age_days': house.current_age_days,
                'status': house.status,
                'is_integrated': house.is_integrated,
                'batch_start_date': house.batch_start_date.isoformat() if house.batch_start_date else None,
                'expected_harvest_date': house.expected_harvest_date.isoformat() if house.expected_harvest_date else None
            })
        
        return {
            'houses': house_data,
            'total_houses': len(house_data)
        }
    
    @staticmethod
    def _generate_task_completion_data(organization, parameters):
        """Generate task completion report data"""
        from tasks.models import Task
        
        tasks = Task.objects.filter(
            house__farm__organization=organization
        )
        
        # Apply filters
        if parameters.get('date_from'):
            tasks = tasks.filter(created_at__gte=parameters['date_from'])
        
        if parameters.get('date_to'):
            tasks = tasks.filter(created_at__lte=parameters['date_to'])
        
        completed_tasks = tasks.filter(is_completed=True).count()
        total_tasks = tasks.count()
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }
    
    @staticmethod
    def _generate_custom_data(template, parameters):
        """Generate custom report data based on template configuration"""
        # This would execute custom queries based on template config
        # For now, return empty data
        return {}
    
    @staticmethod
    def _generate_report_file(template, report_data, export_format):
        """
        Generate report file in specified format
        
        Note: Actual file generation would require libraries like:
        - PDF: reportlab, weasyprint, or xhtml2pdf
        - Excel: openpyxl or xlsxwriter
        - CSV: built-in csv module
        
        This is a placeholder implementation
        """
        # TODO: Implement actual file generation
        # For now, return None to indicate file generation is not yet implemented
        logger.warning(f"Report file generation for format {export_format} not yet implemented")
        return None


class ScheduledReportService:
    """Service for managing scheduled reports"""
    
    @staticmethod
    def schedule_next_run(scheduled_report):
        """Calculate and set next run time for a scheduled report"""
        from reporting.models import ScheduledReport
        
        frequency = scheduled_report.frequency
        schedule_config = scheduled_report.schedule_config or {}
        
        now = timezone.now()
        
        if frequency == 'daily':
            # Run daily at specified time
            run_time = schedule_config.get('time', '09:00')
            hour, minute = map(int, run_time.split(':'))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif frequency == 'weekly':
            # Run weekly on specified day
            day_of_week = schedule_config.get('day_of_week', 0)  # 0=Monday
            run_time = schedule_config.get('time', '09:00')
            hour, minute = map(int, run_time.split(':'))
            
            days_until_next = (day_of_week - now.weekday()) % 7
            if days_until_next == 0 and now.hour >= hour:
                days_until_next = 7
            
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_run += timedelta(days=days_until_next)
        
        elif frequency == 'monthly':
            # Run monthly on specified day
            day_of_month = schedule_config.get('day_of_month', 1)
            run_time = schedule_config.get('time', '09:00')
            hour, minute = map(int, run_time.split(':'))
            
            if now.day >= day_of_month:
                # Next month
                if now.month == 12:
                    next_run = now.replace(year=now.year + 1, month=1, day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    next_run = now.replace(month=now.month + 1, day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
            else:
                # This month
                next_run = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
        
        else:
            # Default: next day
            next_run = now + timedelta(days=1)
        
        scheduled_report.next_run_at = next_run
        scheduled_report.save()
        
        return next_run
    
    @staticmethod
    def get_due_reports():
        """Get scheduled reports that are due to run"""
        from reporting.models import ScheduledReport
        
        now = timezone.now()
        
        due_reports = ScheduledReport.objects.filter(
            status='active',
            next_run_at__lte=now
        )
        
        return due_reports
    
    @staticmethod
    def execute_scheduled_report(scheduled_report):
        """Execute a scheduled report"""
        from reporting.services import ReportGenerationService
        
        try:
            # Generate report
            execution = ReportGenerationService.generate_report_from_template(
                scheduled_report.template,
                parameters=scheduled_report.report_filters,
                export_format=scheduled_report.template.default_format
            )
            
            # Update last run time
            scheduled_report.last_run_at = timezone.now()
            
            # Schedule next run
            ScheduledReportService.schedule_next_run(scheduled_report)
            
            # TODO: Send report to recipients via email
            
            logger.info(f"Executed scheduled report {scheduled_report.id}")
            
            return execution
            
        except Exception as e:
            logger.error(f"Error executing scheduled report {scheduled_report.id}: {str(e)}")
            raise

