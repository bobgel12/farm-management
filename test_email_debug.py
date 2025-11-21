#!/usr/bin/env python3
"""
Comprehensive Email Testing and Debugging Script
Tests email configuration, connection, and sending functionality
"""

import os
import sys
import django
from pathlib import Path
import traceback

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chicken_management.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend
from tasks.email_service import TaskEmailService
from tasks.email_alternatives import EmailService
from farms.models import Farm
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_email_configuration():
    """Test 1: Check email configuration"""
    print_section("TEST 1: Email Configuration Check")
    
    config = {
        'EMAIL_BACKEND': settings.EMAIL_BACKEND,
        'EMAIL_HOST': settings.EMAIL_HOST,
        'EMAIL_PORT': settings.EMAIL_PORT,
        'EMAIL_USE_TLS': settings.EMAIL_USE_TLS,
        'EMAIL_USE_SSL': getattr(settings, 'EMAIL_USE_SSL', False),
        'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
        'EMAIL_HOST_PASSWORD': '***' if settings.EMAIL_HOST_PASSWORD else 'NOT SET',
        'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
        'DEBUG': settings.DEBUG,
    }
    
    for key, value in config.items():
        status = "✅" if value and value != 'NOT SET' else "❌"
        print(f"{status} {key}: {value}")
    
    # Check if using console backend
    if 'console' in settings.EMAIL_BACKEND.lower():
        print("\n⚠️  WARNING: Using console email backend!")
        print("   Emails will be printed to logs, not actually sent.")
        print("   This happens when EMAIL_HOST_USER or EMAIL_HOST_PASSWORD is not set.")
    
    # Check if credentials are set
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("\n⚠️  WARNING: Email credentials are not fully configured!")
        print("   Please set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD")
        print("   See EMAIL_DEBUG_REPORT.md for configuration instructions")
        return False
    
    print("\n✅ Email configuration looks good!")
    return True

def test_smtp_connection():
    """Test 2: Test SMTP connection"""
    print_section("TEST 2: SMTP Connection Test")
    
    try:
        print(f"Attempting to connect to {settings.EMAIL_HOST}:{settings.EMAIL_PORT}...")
        
        backend = EmailBackend(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            use_ssl=getattr(settings, 'EMAIL_USE_SSL', False),
            fail_silently=False,
            timeout=getattr(settings, 'EMAIL_TIMEOUT', 30)
        )
        
        # Test connection
        backend.open()
        print("✅ SMTP connection successful!")
        
        # Test authentication
        if hasattr(backend, 'connection') and backend.connection:
            print("✅ SMTP authentication successful!")
        
        backend.close()
        return True
        
    except Exception as e:
        print(f"❌ SMTP connection failed: {str(e)}")
        print(f"\nError details:")
        traceback.print_exc()
        return False

def test_simple_email_send():
    """Test 3: Send a simple test email"""
    print_section("TEST 3: Simple Email Send Test")
    
    # Check if using console backend
    if 'console' in settings.EMAIL_BACKEND.lower():
        print("⚠️  Using console email backend - email will be printed to logs, not actually sent")
        print("   To actually send emails, configure EMAIL_HOST_USER and EMAIL_HOST_PASSWORD")
        return False
    
    # Use EMAIL_HOST_USER as recipient (send to yourself)
    test_recipient = settings.EMAIL_HOST_USER
    
    if not test_recipient:
        print("❌ Cannot test email send: EMAIL_HOST_USER is not set")
        return False
    
    print(f"Sending test email to: {test_recipient}")
    
    try:
        send_mail(
            subject='Test Email from Chicken House Management',
            message='This is a test email to verify your email configuration is working correctly.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_recipient],
            fail_silently=False,
        )
        print("✅ Test email sent successfully!")
        print(f"   Please check your inbox at {test_recipient}")
        print("   (Also check spam folder if not received)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {str(e)}")
        print(f"\nError details:")
        traceback.print_exc()
        return False

def test_email_service():
    """Test 4: Test EmailService class"""
    print_section("TEST 4: EmailService Class Test")
    
    try:
        test_recipient = settings.EMAIL_HOST_USER
        if not test_recipient:
            print("❌ Cannot test: EMAIL_HOST_USER is not set")
            return False
        
        print(f"Testing EmailService.send_email() to {test_recipient}...")
        
        success = EmailService.send_email(
            recipients=[test_recipient],
            subject='Test Email via EmailService',
            content='This is a test email sent via the EmailService class.',
            html_content='<p>This is a test email sent via the <strong>EmailService</strong> class.</p>'
        )
        
        if success:
            print("✅ EmailService.send_email() succeeded!")
            return True
        else:
            print("❌ EmailService.send_email() returned False")
            return False
            
    except Exception as e:
        print(f"❌ EmailService test failed: {str(e)}")
        print(f"\nError details:")
        traceback.print_exc()
        return False

def test_task_email_service():
    """Test 5: Test TaskEmailService (requires farm with workers)"""
    print_section("TEST 5: TaskEmailService Test")
    
    try:
        # Get first active farm
        farms = Farm.objects.filter(is_active=True)
        
        if not farms.exists():
            print("⚠️  No active farms found. Skipping TaskEmailService test.")
            print("   Create a farm first to test this functionality.")
            return None
        
        farm = farms.first()
        print(f"Testing with farm: {farm.name} (ID: {farm.id})")
        
        # Check for workers
        workers = farm.workers.filter(is_active=True, receive_daily_tasks=True)
        if not workers.exists():
            print("⚠️  No active workers with receive_daily_tasks=True found.")
            print("   Create workers for this farm to test task email functionality.")
            return None
        
        print(f"Found {workers.count()} worker(s) to send test email to")
        test_recipient = settings.EMAIL_HOST_USER
        
        if not test_recipient:
            print("❌ Cannot test: EMAIL_HOST_USER is not set")
            return False
        
        print(f"Sending test email via TaskEmailService to {test_recipient}...")
        
        success, message = TaskEmailService.send_test_email(farm.id, test_recipient)
        
        if success:
            print(f"✅ TaskEmailService test succeeded: {message}")
            return True
        else:
            print(f"❌ TaskEmailService test failed: {message}")
            return False
            
    except Exception as e:
        print(f"❌ TaskEmailService test failed: {str(e)}")
        print(f"\nError details:")
        traceback.print_exc()
        return False

def test_environment_variables():
    """Test 6: Check environment variables"""
    print_section("TEST 6: Environment Variables Check")
    
    env_vars = [
        'EMAIL_HOST',
        'EMAIL_PORT',
        'EMAIL_USE_TLS',
        'EMAIL_HOST_USER',
        'EMAIL_HOST_PASSWORD',
        'DEFAULT_FROM_EMAIL',
        'DISABLE_EMAIL',
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if var == 'EMAIL_HOST_PASSWORD' and value:
            value = '***' + value[-4:] if len(value) > 4 else '***'
        status = "✅" if value else "❌"
        print(f"{status} {var}: {value if value else 'NOT SET'}")
    
    # Check if email is disabled
    if os.getenv('DISABLE_EMAIL', 'False').lower() == 'true':
        print("\n⚠️  WARNING: Email sending is DISABLED (DISABLE_EMAIL=True)")
        return False
    
    return True

def main():
    """Run all email tests"""
    print("\n" + "=" * 70)
    print("  🐔 Chicken House Management - Email Testing & Debugging")
    print("=" * 70)
    
    results = {}
    
    # Test 1: Configuration
    results['configuration'] = test_email_configuration()
    
    # Test 2: Environment variables
    results['environment'] = test_environment_variables()
    
    # Only continue if configuration is valid
    if not results['configuration']:
        print("\n" + "=" * 70)
        print("  ❌ Email configuration is incomplete. Please fix configuration first.")
        print("=" * 70)
        return
    
    # Test 3: SMTP Connection
    results['connection'] = test_smtp_connection()
    
    # Test 4: Simple email send
    if results['connection']:
        results['simple_send'] = test_simple_email_send()
    else:
        print("\n⚠️  Skipping email send tests due to connection failure")
        results['simple_send'] = False
    
    # Test 5: EmailService
    if results['connection']:
        results['email_service'] = test_email_service()
    else:
        results['email_service'] = False
    
    # Test 6: TaskEmailService (optional)
    results['task_email_service'] = test_task_email_service()
    
    # Summary
    print_section("Test Summary")
    
    for test_name, result in results.items():
        if result is None:
            status = "⚠️  SKIPPED"
        elif result:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    # Overall status
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("\n🎉 All email tests passed!")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")
        print("\n💡 Troubleshooting tips:")
        print("   1. Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are set correctly")
        print("   2. For Gmail, use an App Password (not your regular password)")
        print("   3. Check firewall/network restrictions")
        print("   4. Verify SMTP server settings (host, port, TLS)")
        print("   5. Check if DISABLE_EMAIL is set to 'True'")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

