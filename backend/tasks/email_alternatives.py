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
        email_provider = os.getenv('EMAIL_PROVIDER', '').lower()
        
        # Resend is best for low volume (3,000 emails/month free)
        if email_provider == 'resend' or 'resend.com' in email_host.lower():
            return EmailService._send_via_resend(recipients, subject, content, html_content)
        elif 'sendgrid.net' in email_host:
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
            
            # Validate API key
            if not api_key:
                logger.error("SendGrid API key (EMAIL_HOST_PASSWORD) is not set in environment variables")
                return False
            
            if not api_key.startswith('SG.'):
                logger.error(f"Invalid SendGrid API key format. Expected format: SG.xxxxx (got: {api_key[:5]}...)")
                return False
            
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
            
            # Check for 401 specifically
            if response.status_code == 401:
                logger.error("=" * 60)
                logger.error("SendGrid Authentication Failed (401 Unauthorized)")
                logger.error("Possible causes:")
                logger.error("1. API key is incorrect or has been revoked")
                logger.error("2. API key doesn't have 'Mail Send' permission enabled")
                logger.error("3. API key format is invalid")
                logger.error("=" * 60)
                logger.error("To fix:")
                logger.error("1. Go to SendGrid Dashboard → Settings → API Keys")
                logger.error("2. Create a new API key with 'Mail Send' permission")
                logger.error("3. Update EMAIL_HOST_PASSWORD environment variable")
                logger.error("4. Ensure the key starts with 'SG.'")
                logger.error("=" * 60)
                try:
                    error_details = response.json()
                    logger.error(f"SendGrid error details: {error_details}")
                except:
                    logger.error(f"SendGrid error response: {response.text}")
                return False
            
            response.raise_for_status()
            
            logger.info(f"SendGrid email sent successfully to {recipients}")
            return True
            
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 401:
                logger.error("SendGrid authentication failed (401). Check API key and permissions.")
            else:
                logger.error(f"SendGrid HTTP error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"SendGrid email failed: {str(e)}")
            return False
    
    @staticmethod
    def _send_via_resend(recipients, subject, content, html_content=None):
        """Send via Resend API (Best for low volume - 3,000 emails/month free)"""
        try:
            import resend
            
            api_key = os.getenv('RESEND_API_KEY') or os.getenv('EMAIL_HOST_PASSWORD')
            from_email = settings.DEFAULT_FROM_EMAIL
            
            if not api_key:
                logger.error("Resend API key (RESEND_API_KEY or EMAIL_HOST_PASSWORD) is not set")
                return False
            
            resend.api_key = api_key
            
            # Resend supports multiple recipients
            for recipient in recipients:
                params = {
                    "from": from_email,
                    "to": recipient,
                    "subject": subject,
                    "text": content,
                }
                
                if html_content:
                    params["html"] = html_content
                
                email = resend.Emails.send(params)
                
                if email and 'id' in email:
                    logger.info(f"Resend email sent successfully to {recipient} (ID: {email['id']})")
            
            logger.info(f"Resend emails sent successfully to {recipients}")
            return True
            
        except ImportError:
            logger.error("Resend package not installed. Install with: pip install resend")
            return False
        except Exception as e:
            logger.error(f"Resend email failed: {str(e)}")
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
    email_provider = os.getenv('EMAIL_PROVIDER', '').lower()
    print(f"Email Host: {email_host}")
    print(f"Email Provider: {email_provider or 'auto-detect'}")
    
    if email_provider == 'resend' or 'resend.com' in email_host.lower():
        print("📧 Using Resend API (3,000 emails/month free)")
        return "resend"
    elif 'sendgrid.net' in email_host:
        print("📧 Using SendGrid API")
        return "sendgrid"
    elif 'mailgun.org' in email_host:
        print("📧 Using Mailgun API")
        return "mailgun"
    else:
        print("📧 Using SMTP")
        return "smtp"
