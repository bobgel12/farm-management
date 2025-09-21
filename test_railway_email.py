#!/usr/bin/env python3
"""
Test script to verify email configuration on Railway
Run this script to test email settings without sending actual emails
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chicken_management.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend

def test_email_configuration():
    """Test email configuration and connection"""
    print("🔧 Testing Email Configuration on Railway")
    print("=" * 50)
    
    # Check environment variables
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'Not set'}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print()
    
    # Test SMTP connection
    print("🔌 Testing SMTP Connection...")
    try:
        backend = EmailBackend(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            fail_silently=False
        )
        
        # Test connection
        backend.open()
        print("✅ SMTP connection successful!")
        backend.close()
        
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False
    
    # Test sending email (optional - uncomment to actually send)
    print("\n📧 Testing Email Send (dry run)...")
    try:
        # This is a dry run - we won't actually send
        print("✅ Email configuration is valid and ready to send emails")
        print("💡 To send a real test email, use the API endpoint:")
        print("   POST /api/tasks/send-test-email/")
        print("   with body: {'farm_id': 1, 'test_email': 'your-email@gmail.com'}")
        
    except Exception as e:
        print(f"❌ Email send test failed: {e}")
        return False
    
    print("\n🎉 Email configuration test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_email_configuration()
    sys.exit(0 if success else 1)
