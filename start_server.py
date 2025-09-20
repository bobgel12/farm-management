#!/usr/bin/env python3
"""
Startup script for Railway deployment
This script helps debug startup issues
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chicken_management.settings_prod')

def check_environment():
    """Check environment variables"""
    print("🔍 Checking Environment Variables...")
    print("=" * 50)
    
    # Check critical environment variables
    critical_vars = ['SECRET_KEY', 'DATABASE_URL']
    optional_vars = ['ALLOWED_HOSTS', 'CORS_ALLOWED_ORIGINS', 'CSRF_TRUSTED_ORIGINS']
    
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            if var == 'DATABASE_URL':
                print(f"✅ {var}: Set (length: {len(value)})")
            else:
                print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Not set (CRITICAL)")
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Set")
        else:
            print(f"⚠️  {var}: Not set (optional)")
    
    print(f"🌐 PORT: {os.getenv('PORT', 'Not set')}")
    print(f"🐍 PYTHON_VERSION: {sys.version}")

def check_database():
    """Check database connection"""
    print("\n🔍 Checking Database Connection...")
    print("=" * 50)
    
    try:
        import django
        # Setup Django
        django.setup()
        
        from django.db import connection
        from django.conf import settings
        
        # Check database configuration
        db_config = settings.DATABASES['default']
        print(f"📊 Database Engine: {db_config['ENGINE']}")
        print(f"📊 Database Name: {db_config['NAME']}")
        
        if 'HOST' in db_config:
            print(f"📊 Database Host: {db_config['HOST']}")
            print(f"📊 Database Port: {db_config['PORT']}")
        
        # Test connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ Database connection successful! Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_migrations():
    """Run database migrations"""
    print("\n🔍 Running Database Migrations...")
    print("=" * 50)
    
    try:
        import django
        django.setup()
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        print("✅ Migrations completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Migrations failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def start_server():
    """Start the Django development server"""
    print("\n🚀 Starting Django Server...")
    print("=" * 50)
    
    try:
        import django
        django.setup()
        from django.core.management import execute_from_command_line
        
        port = os.getenv('PORT', '8000')
        host = '0.0.0.0'
        
        print(f"🌐 Starting server on {host}:{port}")
        execute_from_command_line([
            'manage.py', 
            'runserver', 
            f'{host}:{port}'
        ])
    except Exception as e:
        print(f"❌ Server startup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Chicken House Management - Railway Startup")
    print("=" * 60)
    
    # Check environment
    check_environment()
    
    # Check database
    db_ok = check_database()
    
    if not db_ok:
        print("\n💥 Database connection failed. Exiting.")
        sys.exit(1)
    
    # Run migrations
    migrate_ok = run_migrations()
    
    if not migrate_ok:
        print("\n💥 Migrations failed. Exiting.")
        sys.exit(1)
    
    # Start server
    print("\n🎉 All checks passed! Starting server...")
    start_server()
