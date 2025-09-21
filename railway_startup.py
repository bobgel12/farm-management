#!/usr/bin/env python
"""
Railway-specific startup script for Chicken House Management System
Handles email configuration and ensures all services are ready
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.core.mail import send_mail
from django.conf import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_email_configuration():
    """Check if email configuration is properly set up"""
    required_vars = [
        'EMAIL_HOST',
        'EMAIL_HOST_USER', 
        'EMAIL_HOST_PASSWORD',
        'DEFAULT_FROM_EMAIL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing email environment variables: {', '.join(missing_vars)}")
        logger.warning("Email functionality will not work until these are configured in Railway dashboard")
        return False
    
    logger.info("Email configuration looks good!")
    return True

def test_email_connection():
    """Test email connection if configured"""
    try:
        # Test SMTP connection
        from django.core.mail import get_connection
        connection = get_connection()
        connection.open()
        connection.close()
        logger.info("✅ Email connection test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Email connection test failed: {str(e)}")
        return False

def setup_database():
    """Set up database migrations"""
    try:
        logger.info("Running database migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        logger.info("✅ Database migrations completed")
        return True
    except Exception as e:
        logger.error(f"❌ Database migration failed: {str(e)}")
        return False

def create_admin_user():
    """Create admin user if it doesn't exist"""
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
            logger.info(f"✅ Admin user '{admin_username}' created")
        else:
            logger.info(f"✅ Admin user '{admin_username}' already exists")
        return True
    except Exception as e:
        logger.error(f"❌ Admin user creation failed: {str(e)}")
        return False

def collect_static_files():
    """Collect static files for production"""
    try:
        logger.info("Collecting static files...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        logger.info("✅ Static files collected")
        return True
    except Exception as e:
        logger.error(f"❌ Static files collection failed: {str(e)}")
        return False

def main():
    """Main startup function"""
    logger.info("🐔 Starting Chicken House Management System on Railway...")
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chicken_management.settings')
    django.setup()
    
    # Check environment
    logger.info(f"Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'development')}")
    logger.info(f"Database URL: {'Set' if os.getenv('DATABASE_URL') else 'Not set'}")
    
    # Set up database
    if not setup_database():
        logger.error("Failed to set up database. Exiting...")
        sys.exit(1)
    
    # Create admin user
    if not create_admin_user():
        logger.error("Failed to create admin user. Continuing anyway...")
    
    # Collect static files
    if not collect_static_files():
        logger.error("Failed to collect static files. Continuing anyway...")
    
    # Check email configuration
    email_configured = check_email_configuration()
    if email_configured:
        test_email_connection()
    
    # Log configuration summary
    logger.info("📧 Email Configuration:")
    logger.info(f"  Host: {os.getenv('EMAIL_HOST', 'Not set')}")
    logger.info(f"  Port: {os.getenv('EMAIL_PORT', 'Not set')}")
    logger.info(f"  User: {os.getenv('EMAIL_HOST_USER', 'Not set')}")
    logger.info(f"  TLS: {os.getenv('EMAIL_USE_TLS', 'Not set')}")
    logger.info(f"  From: {os.getenv('DEFAULT_FROM_EMAIL', 'Not set')}")
    
    # Start the server
    logger.info("🚀 Starting Django development server...")
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])

if __name__ == '__main__':
    main()
