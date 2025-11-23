"""
Celery tasks for scheduled report generation
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def execute_due_scheduled_reports():
    """Execute all scheduled reports that are due to run"""
    from reporting.services import ScheduledReportService
    
    try:
        due_reports = ScheduledReportService.get_due_reports()
        
        if not due_reports.exists():
            logger.info("No scheduled reports due for execution")
            return
        
        logger.info(f"Found {due_reports.count()} scheduled reports due for execution")
        
        for scheduled_report in due_reports:
            try:
                ScheduledReportService.execute_scheduled_report(scheduled_report)
                logger.info(f"Successfully executed scheduled report {scheduled_report.id}")
            except Exception as e:
                logger.error(f"Error executing scheduled report {scheduled_report.id}: {str(e)}")
                # Continue with next report even if one fails
        
    except Exception as e:
        logger.error(f"Error in execute_due_scheduled_reports task: {str(e)}")
        raise


@shared_task
def generate_report(report_template_id, parameters=None, export_format='pdf'):
    """
    Generate a report asynchronously
    
    Args:
        report_template_id: ID of the ReportTemplate
        parameters: Report parameters dict
        export_format: Export format (pdf, excel, csv, etc.)
    """
    from reporting.models import ReportTemplate
    from reporting.services import ReportGenerationService
    
    try:
        template = ReportTemplate.objects.get(id=report_template_id)
        
        execution = ReportGenerationService.generate_report_from_template(
            template,
            parameters=parameters,
            export_format=export_format
        )
        
        logger.info(f"Generated report execution {execution.id}")
        return execution.id
        
    except ReportTemplate.DoesNotExist:
        logger.error(f"ReportTemplate {report_template_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise


@shared_task
def calculate_organization_kpis(organization_id, calculation_date=None):
    """
    Calculate KPIs for an organization
    
    Args:
        organization_id: ID of the Organization
        calculation_date: Date for calculation (defaults to today)
    """
    from organizations.models import Organization
    from analytics.models import KPI, KPICalculation
    from analytics.services import KPICalculationService
    
    try:
        organization = Organization.objects.get(id=organization_id)
        
        if not calculation_date:
            calculation_date = timezone.now().date()
        
        # Get all active KPIs for the organization
        kpis = KPI.objects.filter(
            organization=organization,
            is_active=True
        )
        
        logger.info(f"Calculating KPIs for organization {organization.name}")
        
        calculations_created = 0
        
        for kpi in kpis:
            try:
                # Calculate KPI value
                value = KPICalculationService.calculate_organization_kpi(
                    organization,
                    {
                        'metric_type': kpi.metric_type,
                        'calculation_config': kpi.calculation_config
                    },
                    calculation_date
                )
                
                if value is not None:
                    # Get previous value for comparison
                    previous_calculation = KPICalculation.objects.filter(
                        kpi=kpi,
                        calculation_date__lt=calculation_date
                    ).order_by('-calculation_date').first()
                    
                    previous_value = previous_calculation.value if previous_calculation else None
                    change_percentage = None
                    
                    if previous_value and previous_value > 0:
                        change_percentage = ((value - previous_value) / previous_value) * 100
                    
                    # Determine status based on thresholds
                    status = 'normal'
                    if kpi.critical_threshold:
                        if (kpi.metric_type in ['mortality_rate'] and value > kpi.critical_threshold) or \
                           (kpi.metric_type not in ['mortality_rate'] and value < kpi.critical_threshold):
                            status = 'critical'
                        elif kpi.warning_threshold:
                            if (kpi.metric_type in ['mortality_rate'] and value > kpi.warning_threshold) or \
                               (kpi.metric_type not in ['mortality_rate'] and value < kpi.warning_threshold):
                                status = 'warning'
                    
                    # Create or update calculation
                    calculation, created = KPICalculation.objects.update_or_create(
                        kpi=kpi,
                        calculation_date=calculation_date,
                        organization=organization,
                        filters={},  # Default filters
                        defaults={
                            'value': value,
                            'unit': kpi.unit,
                            'previous_value': previous_value,
                            'change_percentage': change_percentage,
                            'status': status,
                            'calculated_by': None  # System calculation
                        }
                    )
                    
                    if created:
                        calculations_created += 1
                    
                    logger.info(f"Calculated KPI {kpi.name}: {value} {kpi.unit}")
                
            except Exception as e:
                logger.error(f"Error calculating KPI {kpi.id}: {str(e)}")
                continue
        
        logger.info(f"Created {calculations_created} KPI calculations for organization {organization.name}")
        
    except Organization.DoesNotExist:
        logger.error(f"Organization {organization_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error calculating organization KPIs: {str(e)}")
        raise

