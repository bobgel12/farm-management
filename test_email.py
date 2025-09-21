#!/usr/bin/env python3
"""
Email Configuration Test Script
Run this to test your email setup
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chicken_management.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives

def test_email_config():
    """Test email configuration"""
    print("🐔 Chicken House Management - Email Configuration Test")
    print("=" * 60)
    
    # Check configuration
    print(f"📧 Email Backend: {settings.EMAIL_BACKEND}")
    print(f"📧 Email Host: {settings.EMAIL_HOST}")
    print(f"📧 Email Port: {settings.EMAIL_PORT}")
    print(f"📧 Email User: {settings.EMAIL_HOST_USER}")
    print(f"📧 Email Password: {'***' if settings.EMAIL_HOST_PASSWORD else 'Not set'}")
    print(f"📧 From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"🐛 Debug Mode: {settings.DEBUG}")
    
    print("\n" + "=" * 60)
    
    # Test email sending
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("❌ Email credentials not configured!")
        print("📝 Please set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD")
        return False
    
    try:
        # Test simple email
        print("📤 Testing email sending...")
        send_mail(
            'Test Email from Chicken House Management',
            'This is a test email to verify your configuration.',
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER],  # Send to yourself
            fail_silently=False,
        )
        print("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_email_config()
    if success:
        print("\n🎉 Email configuration is working correctly!")
    else:
        print("\n🔧 Please check your email configuration and try again.")
        print("📚 See EMAIL_SETUP_COMPLETE.md for detailed instructions.")
