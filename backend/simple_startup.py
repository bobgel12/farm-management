#!/usr/bin/env python3
"""
Simple startup script for Railway deployment
Handles missing environment variables gracefully
"""
import os
import sys
import django
from pathlib import Path

# Add the current directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chicken_management.settings_prod')

def setup_environment():
    """Set up required environment variables if missing"""
    print("🔧 Setting up environment variables...")
    
    # Set SECRET_KEY if not provided
    if not os.getenv('SECRET_KEY'):
        # Generate a simple secret key for development
        secret_key = 'django-insecure-railway-dev-key-' + os.urandom(32).hex()
        os.environ['SECRET_KEY'] = secret_key
        print("⚠️  SECRET_KEY not set, using generated key for development")
    
    # Set DEBUG if not provided
    if not os.getenv('DEBUG'):
        os.environ['DEBUG'] = 'False'
        print("✅ DEBUG set to False")
    
    # Set ALLOWED_HOSTS if not provided
    if not os.getenv('ALLOWED_HOSTS'):
        os.environ['ALLOWED_HOSTS'] = '*'
        print("✅ ALLOWED_HOSTS set to *")
    
    print(f"🔑 SECRET_KEY: {'Set' if os.getenv('SECRET_KEY') else 'Not set'}")
    print(f"🗄️  DATABASE_URL: {'Set' if os.getenv('DATABASE_URL') else 'Not set (using SQLite)'}")
    print(f"🌐 PORT: {os.getenv('PORT', '8000')}")

def test_database():
    """Test database connection"""
    print("\n🔍 Testing database connection...")
    
    try:
        django.setup()
        from django.db import connection
        from django.conf import settings
        
        db_config = settings.DATABASES['default']
        print(f"📊 Database: {db_config['ENGINE']}")
        print(f"📊 Name: {db_config['NAME']}")
        
        # Test connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ Database connection successful: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def run_migrations():
    """Run database migrations"""
    print("\n🔄 Running migrations...")
    
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        print("✅ Migrations completed")
        return True
        
    except Exception as e:
        print(f"❌ Migrations failed: {str(e)}")
        return False

def start_server():
    """Start the Django server"""
    print("\n🚀 Starting Django server...")
    
    try:
        from django.core.management import execute_from_command_line
        
        port = os.getenv('PORT', '8000')
        host = '0.0.0.0'
        
        print(f"🌐 Server starting on {host}:{port}")
        print(f"🔗 Health check: http://{host}:{port}/api/health/")
        
        execute_from_command_line([
            'manage.py', 
            'runserver', 
            f'{host}:{port}'
        ])
        
    except Exception as e:
        print(f"❌ Server startup failed: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main startup function"""
    print("🚀 Chicken House Management - Simple Startup")
    print("=" * 60)
    
    # Setup environment
    setup_environment()
    
    # Test database
    if not test_database():
        print("\n💥 Database test failed, but continuing with startup...")
    
    # Run migrations
    if not run_migrations():
        print("\n💥 Migrations failed, but continuing with startup...")
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
