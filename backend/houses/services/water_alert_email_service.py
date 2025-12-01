"""
Email service for water consumption alerts
"""
import logging
import os
from typing import List
from django.conf import settings
from django.contrib.auth import get_user_model
from organizations.models import OrganizationUser
from houses.models import House, WaterConsumptionAlert
from tasks.email_service import TaskEmailService

logger = logging.getLogger(__name__)
User = get_user_model()


class WaterAlertEmailService:
    """Service to send email alerts for water consumption anomalies"""
    
    @staticmethod
    def send_alert_email(alert: WaterConsumptionAlert) -> bool:
        """
        Send email alert for water consumption anomaly
        
        Args:
            alert: WaterConsumptionAlert instance
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Get recipients (organization admins, managers, and owners)
            recipients = WaterAlertEmailService._get_alert_recipients(alert.house)
            
            if not recipients:
                logger.warning(f"No recipients found for water alert {alert.id}")
                return False
            
            # Generate email content
            subject = f"🚨 Water Consumption Alert - House {alert.house.house_number} ({alert.severity.upper()})"
            text_content, html_content = WaterAlertEmailService._generate_email_content(alert)
            
            # Send email using TaskEmailService (which uses Resend)
            success = TaskEmailService._send_via_resend(
                recipients=recipients,
                subject=subject,
                text_content=text_content,
                html_content=html_content
            )
            
            if success:
                # Update alert record
                from django.utils import timezone
                alert.email_sent = True
                alert.email_sent_at = timezone.now()
                alert.email_recipients = recipients
                alert.save()
                logger.info(f"Water consumption alert email sent successfully for alert {alert.id} to {len(recipients)} recipients")
            
            return success
        
        except Exception as e:
            logger.error(f"Error sending water consumption alert email for alert {alert.id}: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def _get_alert_recipients(house: House) -> List[str]:
        """
        Get list of email addresses to receive water consumption alerts
        
        Returns recipients from:
        - Organization owners, admins, and managers
        - Farm workers (who receive daily tasks)
        - Farm contact email
        """
        recipients = []
        
        try:
            # Get organization from farm
            if house.farm and house.farm.organization:
                organization = house.farm.organization
                
                # Get organization users with appropriate roles
                org_users = OrganizationUser.objects.filter(
                    organization=organization,
                    is_active=True
                ).select_related('user')
                
                # Filter by role (owners, admins, managers)
                for org_user in org_users:
                    if org_user.role in ['owner', 'admin', 'manager']:
                        if org_user.user and org_user.user.email:
                            recipients.append(org_user.user.email)
            
            # Get farm workers who receive daily tasks
            if house.farm:
                from farms.models import Worker
                farm_workers = Worker.objects.filter(
                    farm=house.farm,
                    is_active=True,
                    receive_daily_tasks=True
                )
                
                for worker in farm_workers:
                    if worker.email and worker.email not in recipients:
                        recipients.append(worker.email)
                
                # Also include farm contact email if available
                if house.farm.contact_email and house.farm.contact_email not in recipients:
                    recipients.append(house.farm.contact_email)
            
            # Remove duplicates
            recipients = list(set(recipients))
            
            logger.info(f"Found {len(recipients)} recipients for water alert: {recipients}")
        
        except Exception as e:
            logger.error(f"Error getting alert recipients: {str(e)}", exc_info=True)
        
        return recipients
    
    @staticmethod
    def _build_comparison_section(avg_water_7d, farm_avg_water, alert):
        """Build HTML section for water consumption comparison"""
        farm_avg_html = f'''
            <div class="metric">
                <div class="metric-label">Farm Average</div>
                <div class="metric-value">{farm_avg_water:.2f} L/day</div>
            </div>
        ''' if farm_avg_water else '<div></div>'
        
        return f'''
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0;">
            <div class="metric">
                <div class="metric-label">7-Day Average</div>
                <div class="metric-value">{avg_water_7d:.2f} L/day</div>
            </div>
            {farm_avg_html}
            <div class="metric">
                <div class="metric-label">Difference from Baseline</div>
                <div class="metric-value">+{alert.current_consumption - alert.baseline_consumption:.2f} L</div>
            </div>
        </div>
        '''
    
    @staticmethod
    def _build_environmental_section(latest_snapshot):
        """Build HTML section for current environmental conditions"""
        temp_cell = f'<td style="padding: 5px;"><strong>Temperature:</strong> {latest_snapshot.average_temperature:.1f}°C</td>' if latest_snapshot.average_temperature is not None else '<td></td>'
        humidity_cell = f'<td style="padding: 5px;"><strong>Humidity:</strong> {latest_snapshot.humidity:.1f}%</td>' if latest_snapshot.humidity is not None else '<td></td>'
        bird_cell = f'<td style="padding: 5px;"><strong>Bird Count:</strong> {latest_snapshot.bird_count:,}</td>' if latest_snapshot.bird_count is not None else '<td></td>'
        growth_cell = f'<td style="padding: 5px;"><strong>Growth Day:</strong> {latest_snapshot.growth_day}</td>' if latest_snapshot.growth_day is not None else '<td></td>'
        feed_cell = f'<td style="padding: 5px;"><strong>Feed Consumption:</strong> {latest_snapshot.feed_consumption:.2f} kg/day</td>' if latest_snapshot.feed_consumption is not None else '<td></td>'
        pressure_cell = f'<td style="padding: 5px;"><strong>Static Pressure:</strong> {latest_snapshot.static_pressure:.2f} Pa</td>' if latest_snapshot.static_pressure is not None else '<td></td>'
        
        return f'''
        <div style="margin-top: 20px; padding: 15px; background-color: #f0f0f0; border-radius: 4px;">
            <strong>📊 Current Environmental Conditions:</strong>
            <table style="width: 100%; margin-top: 10px; border-collapse: collapse;">
                <tr>
                    {temp_cell}
                    {humidity_cell}
                </tr>
                <tr>
                    {bird_cell}
                    {growth_cell}
                </tr>
                <tr>
                    {feed_cell}
                    {pressure_cell}
                </tr>
            </table>
        </div>
        '''
    
    @staticmethod
    def _build_historical_section(avg_temp_7d, avg_humidity_7d, avg_water_7d):
        """Build HTML section for historical comparison"""
        items = []
        if avg_temp_7d:
            items.append(f'<li>Average Temperature: {avg_temp_7d:.1f}°C</li>')
        if avg_humidity_7d:
            items.append(f'<li>Average Humidity: {avg_humidity_7d:.1f}%</li>')
        if avg_water_7d:
            items.append(f'<li>Average Water Consumption: {avg_water_7d:.2f} L/day</li>')
        
        items_html = ''.join(items)
        
        return f'''
        <div style="margin-top: 20px; padding: 15px; background-color: #e8f4f8; border-radius: 4px;">
            <strong>📈 Historical Comparison (Last 7 Days):</strong>
            <ul style="margin: 10px 0; padding-left: 20px;">
                {items_html}
            </ul>
        </div>
        '''
    
    @staticmethod
    def _generate_email_content(alert: WaterConsumptionAlert) -> tuple:
        """
        Generate email content (text and HTML) for water consumption alert
        
        Returns:
            Tuple of (text_content, html_content)
        """
        from houses.models import HouseMonitoringSnapshot
        from django.db.models import Avg, Q
        from datetime import timedelta
        from django.utils import timezone
        
        house = alert.house
        farm = alert.farm
        
        # Get latest monitoring snapshot for context
        latest_snapshot = HouseMonitoringSnapshot.objects.filter(
            house=house
        ).order_by('-timestamp').first()
        
        # Get historical data for comparison (last 7 days)
        seven_days_ago = alert.alert_date - timedelta(days=7)
        historical_snapshots = HouseMonitoringSnapshot.objects.filter(
            house=house,
            timestamp__date__gte=seven_days_ago,
            timestamp__date__lte=alert.alert_date
        )
        
        avg_temp_7d = historical_snapshots.aggregate(Avg('average_temperature'))['average_temperature__avg']
        avg_humidity_7d = historical_snapshots.aggregate(Avg('humidity'))['humidity__avg']
        avg_water_7d = historical_snapshots.aggregate(Avg('water_consumption'))['water_consumption__avg']
        
        # Get comparison with other houses in the same farm
        other_houses_snapshots = HouseMonitoringSnapshot.objects.filter(
            house__farm=farm,
            house__farm__has_system_integration=True,
            timestamp__date=alert.alert_date
        ).exclude(house=house)
        
        farm_avg_water = other_houses_snapshots.aggregate(Avg('water_consumption'))['water_consumption__avg'] if other_houses_snapshots.exists() else None
        
        # Severity color mapping
        severity_colors = {
            'low': '#FFA500',  # Orange
            'medium': '#FF6B6B',  # Red
            'high': '#DC143C',  # Crimson
            'critical': '#8B0000',  # Dark Red
        }
        color = severity_colors.get(alert.severity, '#666666')
        
        # Build detailed context information
        context_info = []
        if latest_snapshot:
            if latest_snapshot.average_temperature is not None:
                context_info.append(f"Current Temperature: {latest_snapshot.average_temperature:.1f}°C")
            if latest_snapshot.humidity is not None:
                context_info.append(f"Current Humidity: {latest_snapshot.humidity:.1f}%")
            if latest_snapshot.bird_count is not None:
                context_info.append(f"Bird Count: {latest_snapshot.bird_count:,}")
            if latest_snapshot.growth_day is not None:
                context_info.append(f"Growth Day: {latest_snapshot.growth_day}")
            if latest_snapshot.feed_consumption is not None:
                context_info.append(f"Feed Consumption: {latest_snapshot.feed_consumption:.2f} kg/day")
        
        if avg_temp_7d:
            context_info.append(f"7-Day Avg Temperature: {avg_temp_7d:.1f}°C")
        if avg_humidity_7d:
            context_info.append(f"7-Day Avg Humidity: {avg_humidity_7d:.1f}%")
        if avg_water_7d:
            context_info.append(f"7-Day Avg Water: {avg_water_7d:.2f} L/day")
        
        if farm_avg_water:
            context_info.append(f"Farm Average (Other Houses): {farm_avg_water:.2f} L/day")
        
        context_text = "\n".join(context_info) if context_info else "No additional context data available"
        
        # Text content
        alert_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        text_content = f"""
WATER CONSUMPTION ALERT - {alert.severity.upper()}

Farm: {farm.name}
House: {house.house_number}
Date: {alert.alert_date.strftime('%Y-%m-%d')}
Alert Time: {alert_time}
{'Growth Day: ' + str(alert.growth_day) if alert.growth_day else ''}

═══════════════════════════════════════════════════════════
CONSUMPTION DATA
═══════════════════════════════════════════════════════════
Current Consumption: {alert.current_consumption:.2f} L/day
{('Expected Consumption (Age-Adjusted): ' + f'{alert.expected_consumption:.2f} L/day') if alert.expected_consumption else ('Baseline Average: ' + f'{alert.baseline_consumption:.2f} L/day')}
Increase: {alert.increase_percentage:.1f}% above baseline
Absolute Increase: +{alert.current_consumption - alert.baseline_consumption:.2f} L/day
{('Deviation from Expected: ' + f'{((alert.current_consumption - alert.expected_consumption) / alert.expected_consumption * 100):.1f}%') if alert.expected_consumption else ''}
{'7-Day Average: ' + f'{avg_water_7d:.2f} L/day' if avg_water_7d else ''}
{'Farm Average (Other Houses): ' + f'{farm_avg_water:.2f} L/day' if farm_avg_water else ''}

═══════════════════════════════════════════════════════════
ENVIRONMENTAL CONTEXT
═══════════════════════════════════════════════════════════
{context_text}

═══════════════════════════════════════════════════════════
ANOMALY DETAILS
═══════════════════════════════════════════════════════════
{alert.message}

═══════════════════════════════════════════════════════════
POSSIBLE CAUSES
═══════════════════════════════════════════════════════════
- Water leak or equipment malfunction
- Increased bird activity or stress
- Environmental factors (high temperature/humidity)
- Equipment calibration issues
- Feed quality changes
- Disease/health issues in the flock

═══════════════════════════════════════════════════════════
IMMEDIATE ACTION STEPS
═══════════════════════════════════════════════════════════
1. Inspect water lines and equipment for leaks
2. Check water meter readings
3. Review bird behavior and health status
4. Compare with other houses in the farm
5. Verify environmental conditions
6. Check equipment status and recent maintenance
7. Document findings and corrective actions

═══════════════════════════════════════════════════════════
Please investigate this issue immediately.

Alert ID: {alert.id}
Detection Method: {alert.detection_method}
"""
        
        # HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .alert-box {{
            border-left: 4px solid {color};
            background-color: #f9f9f9;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .severity-badge {{
            display: inline-block;
            background-color: {color};
            color: white;
            padding: 5px 15px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 15px;
        }}
        .metric {{
            margin: 10px 0;
            padding: 10px;
            background-color: white;
            border-radius: 4px;
        }}
        .metric-label {{
            font-weight: bold;
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .metric-value {{
            font-size: 24px;
            color: {color};
            font-weight: bold;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="alert-box">
        <div class="severity-badge">{alert.severity.upper()} ALERT</div>
        <h2 style="margin-top: 0;">Water Consumption Anomaly Detected</h2>
        
        <div style="margin: 20px 0;">
            <strong>Farm:</strong> {farm.name}<br>
            <strong>House:</strong> {house.house_number}<br>
            <strong>Date:</strong> {alert.alert_date.strftime('%Y-%m-%d')}<br>
            {f'<strong>Growth Day:</strong> {alert.growth_day}<br>' if alert.growth_day else ''}
            {f'<strong>Alert Time:</strong> {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}<br>' if True else ''}
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0;">
            <div class="metric">
                <div class="metric-label">Current Consumption</div>
                <div class="metric-value">{alert.current_consumption:.2f} L/day</div>
            </div>
            
            {f'''
            <div class="metric">
                <div class="metric-label">Expected (Age-Adjusted)</div>
                <div class="metric-value">{alert.expected_consumption:.2f} L/day</div>
            </div>
            ''' if alert.expected_consumption else '''
            <div class="metric">
                <div class="metric-label">Baseline Average</div>
                <div class="metric-value">{alert.baseline_consumption:.2f} L/day</div>
            </div>
            '''}
            
            <div class="metric">
                <div class="metric-label">Increase</div>
                <div class="metric-value">+{alert.increase_percentage:.1f}%</div>
            </div>
        </div>
        
        {f'''
        <div style="margin-top: 15px; padding: 10px; background-color: #e3f2fd; border-radius: 4px; border-left: 3px solid #2196f3;">
            <strong>📊 Age-Adjusted Analysis:</strong>
            <p style="margin: 5px 0;">
                Expected consumption for Day {alert.growth_day if alert.growth_day else 'N/A'}: 
                <strong>{alert.expected_consumption:.2f} L/day</strong>
            </p>
            <p style="margin: 5px 0;">
                Deviation from expected: 
                <strong style="color: {color};">{((alert.current_consumption - alert.expected_consumption) / alert.expected_consumption * 100):.1f}%</strong>
            </p>
            <p style="margin: 5px 0; font-size: 12px; color: #666;">
                This baseline accounts for normal age-related increases in water consumption. 
                The alert is based on deviation from age-expected values, not just historical averages.
            </p>
        </div>
        ''' if alert.expected_consumption else ''}
        
        {WaterAlertEmailService._build_comparison_section(avg_water_7d, farm_avg_water, alert) if avg_water_7d else ''}
        
        {WaterAlertEmailService._build_environmental_section(latest_snapshot) if latest_snapshot else ''}
        
        {WaterAlertEmailService._build_historical_section(avg_temp_7d, avg_humidity_7d, avg_water_7d) if (avg_temp_7d or avg_humidity_7d or avg_water_7d) else ''}
        
        <div style="margin-top: 20px; padding: 15px; background-color: #fff3cd; border-radius: 4px;">
            <strong>⚠️ Possible Causes (Based on {alert.increase_percentage:.1f}% Increase):</strong>
            <ul style="margin: 10px 0; padding-left: 20px;">
                <li><strong>Water Leak:</strong> Check all water lines, connections, and drinker systems for visible leaks</li>
                <li><strong>Equipment Malfunction:</strong> Verify water meters, pumps, and pressure regulators are functioning correctly</li>
                <li><strong>Bird Stress/Activity:</strong> Review bird behavior, health status, and any recent changes in management</li>
                <li><strong>Environmental Factors:</strong> High temperature or humidity may increase water consumption - verify climate control</li>
                <li><strong>Equipment Calibration:</strong> Water meters may need recalibration if readings seem inconsistent</li>
                <li><strong>Feed Quality:</strong> Changes in feed composition can affect water intake</li>
                <li><strong>Disease/Health Issues:</strong> Increased water consumption can indicate health problems in the flock</li>
            </ul>
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background-color: #d1ecf1; border-radius: 4px;">
            <strong>📋 Immediate Action Steps:</strong>
            <ol style="margin: 10px 0; padding-left: 20px;">
                <li><strong>Physical Inspection:</strong> Walk through House {house.house_number} and visually inspect all water lines, connections, and drinker systems</li>
                <li><strong>Check Water Meters:</strong> Verify actual meter readings match system data - note any discrepancies</li>
                <li><strong>Review Bird Health:</strong> Check for signs of stress, disease, or unusual behavior patterns</li>
                <li><strong>Compare with Other Houses:</strong> Check if other houses in {farm.name} show similar patterns</li>
                <li><strong>Environmental Check:</strong> Verify temperature and humidity are within normal ranges for growth day {alert.growth_day if alert.growth_day else 'N/A'}</li>
                <li><strong>Equipment Status:</strong> Check if any equipment maintenance or changes occurred recently</li>
                <li><strong>Document Findings:</strong> Record observations and any corrective actions taken</li>
            </ol>
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background-color: #f8d7da; border-radius: 4px; border-left: 4px solid {color};">
            <strong>🔍 Investigation Checklist:</strong>
            <table style="width: 100%; margin-top: 10px; border-collapse: collapse;">
                <tr>
                    <td style="padding: 5px;">☐ Water lines inspected for leaks</td>
                    <td style="padding: 5px;">☐ Water meters verified</td>
                </tr>
                <tr>
                    <td style="padding: 5px;">☐ Drinker systems functioning</td>
                    <td style="padding: 5px;">☐ Bird health assessed</td>
                </tr>
                <tr>
                    <td style="padding: 5px;">☐ Environmental conditions checked</td>
                    <td style="padding: 5px;">☐ Equipment status reviewed</td>
                </tr>
            </table>
        </div>
    </div>
    
    <div class="footer">
        <p>This is an automated alert from the Chicken House Management System.</p>
        <p>Detection Method: {alert.detection_method}</p>
        <p>Alert ID: {alert.id}</p>
    </div>
</body>
</html>
"""
        
        return text_content, html_content

