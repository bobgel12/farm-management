#!/usr/bin/env python
"""
Simple startup script for Railway deployment
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Main startup function"""
    print("🐔 Starting Chicken House Management System...")
    
    # Set up Django
    # Use production settings for Railway deployment
    if os.getenv('RAILWAY_ENVIRONMENT'):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chicken_management.settings_prod')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chicken_management.settings')
    django.setup()
    
    # Run migrations
    print("Running database migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Create admin user if it doesn't exist
    try:
        from django.contrib.auth.models import User
        
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@chickenmanagement.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password
            )
            print(f"✅ Admin user '{admin_username}' created")
        else:
            print(f"✅ Admin user '{admin_username}' already exists")
    except Exception as e:
        print(f"❌ Admin user creation failed: {str(e)}")
    
    # Ensure default program exists
    print("Ensuring default program exists...")
    try:
        execute_from_command_line(['manage.py', 'ensure_default_program'])
        print("✅ Default program ensured")
    except Exception as e:
        print(f"❌ Default program creation failed: {str(e)}")
    
    # Collect static files
    print("Collecting static files...")
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    
    # Check email configuration
    print("📧 Email Configuration:")
    print(f"  Host: {os.getenv('EMAIL_HOST', 'Not set')}")
    print(f"  Port: {os.getenv('EMAIL_PORT', 'Not set')}")
    print(f"  User: {os.getenv('EMAIL_HOST_USER', 'Not set')}")
    print(f"  TLS: {os.getenv('EMAIL_USE_TLS', 'Not set')}")
    print(f"  From: {os.getenv('DEFAULT_FROM_EMAIL', 'Not set')}")
    
    if not os.getenv('EMAIL_HOST_USER') or not os.getenv('EMAIL_HOST_PASSWORD'):
        print("⚠️  Email credentials not configured. Daily emails will not work.")
        print("   Please set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in Railway dashboard.")
    else:
        # Test SMTP connectivity
        print("🔍 Testing SMTP connectivity...")
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex(('smtp.gmail.com', 587))
            sock.close()
            
            if result == 0:
                print("✅ SMTP server is reachable")
            else:
                print(f"❌ SMTP server is not reachable (error code: {result})")
                print("   This may be due to Railway network restrictions.")
        except Exception as e:
            print(f"❌ SMTP connectivity test failed: {str(e)}")
            print("   This may be due to Railway network restrictions.")
    
    # Start the server
    print("🚀 Starting Django development server...")
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])

if __name__ == '__main__':
    main()
