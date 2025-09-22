"""
Alternative email services for Railway deployment
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Unified email service that works with multiple providers"""
    
    @staticmethod
    def send_email(recipients, subject, content, html_content=None):
        """Send email using the configured provider"""
        
        # Check which email service to use
        email_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        
        if 'sendgrid.net' in email_host:
            return EmailService._send_via_sendgrid(recipients, subject, content, html_content)
        elif 'mailgun.org' in email_host:
            return EmailService._send_via_mailgun(recipients, subject, content, html_content)
        else:
            return EmailService._send_via_smtp(recipients, subject, content, html_content)
    
    @staticmethod
    def _send_via_smtp(recipients, subject, content, html_content=None):
        """Send via standard SMTP (Gmail, etc.)"""
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = settings.DEFAULT_FROM_EMAIL
            message['To'] = ', '.join(recipients)
            
            # Add text content
            text_part = MIMEText(content, 'plain')
            message.attach(text_part)
            
            # Add HTML content if provided
            if html_content:
                html_part = MIMEText(html_content, 'html')
                message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                if settings.EMAIL_USE_TLS:
                    server.starttls()
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.send_message(message)
            
            logger.info(f"Email sent successfully to {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP email failed: {str(e)}")
            return False
    
    @staticmethod
    def _send_via_sendgrid(recipients, subject, content, html_content=None):
        """Send via SendGrid API"""
        try:
            import requests
            
            api_key = os.getenv('EMAIL_HOST_PASSWORD')  # SendGrid API key
            from_email = settings.DEFAULT_FROM_EMAIL
            
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "personalizations": [{
                    "to": [{"email": email} for email in recipients]
                }],
                "from": {"email": from_email},
                "subject": subject,
                "content": [
                    {
                        "type": "text/plain",
                        "value": content
                    }
                ]
            }
            
            # Add HTML content if provided
            if html_content:
                data["content"].append({
                    "type": "text/html",
                    "value": html_content
                })
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            logger.info(f"SendGrid email sent successfully to {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"SendGrid email failed: {str(e)}")
            return False
    
    @staticmethod
    def _send_via_mailgun(recipients, subject, content, html_content=None):
        """Send via Mailgun API"""
        try:
            import requests
            
            api_key = os.getenv('EMAIL_HOST_PASSWORD')  # Mailgun API key
            domain = os.getenv('MAILGUN_DOMAIN', 'your-domain.mailgun.org')
            from_email = settings.DEFAULT_FROM_EMAIL
            
            url = f"https://api.mailgun.net/v3/{domain}/messages"
            auth = ("api", api_key)
            
            data = {
                "from": from_email,
                "to": recipients,
                "subject": subject,
                "text": content
            }
            
            if html_content:
                data["html"] = html_content
            
            response = requests.post(url, auth=auth, data=data)
            response.raise_for_status()
            
            logger.info(f"Mailgun email sent successfully to {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"Mailgun email failed: {str(e)}")
            return False

def test_email_connectivity():
    """Test which email service is available"""
    print("🔍 Testing Email Connectivity")
    print("=" * 50)
    
    email_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    print(f"Email Host: {email_host}")
    
    if 'sendgrid.net' in email_host:
        print("📧 Using SendGrid API")
        return "sendgrid"
    elif 'mailgun.org' in email_host:
        print("📧 Using Mailgun API")
        return "mailgun"
    else:
        print("📧 Using SMTP")
        return "smtp"
