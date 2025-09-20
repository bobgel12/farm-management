#!/usr/bin/env python3
"""
Railway startup script with database connection verification
"""
import os
import sys
import time
from pathlib import Path

# Add the current directory to Python path (we're already in backend/)
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chicken_management.settings_prod')

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_environment():
    """Check environment variables"""
    print_header("ENVIRONMENT CHECK")
    
    # Check critical environment variables
    critical_vars = {
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'PORT': os.getenv('PORT', '8000')
    }
    
    for var, value in critical_vars.items():
        if value:
            if var == 'DATABASE_URL':
                print(f"✅ {var}: Set (length: {len(value)})")
                # Show first part of DATABASE_URL for debugging
                if 'postgres://' in value:
                    print(f"   📊 Database type: PostgreSQL")
                elif 'postgresql://' in value:
                    print(f"   📊 Database type: PostgreSQL")
                else:
                    print(f"   📊 Database type: Unknown")
            else:
                print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Not set")
    
    print(f"🌐 Python version: {sys.version}")
    print(f"🌐 Working directory: {os.getcwd()}")

def test_database_connection():
    """Test database connection with retries"""
    print_header("DATABASE CONNECTION TEST")
    
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 Attempt {attempt + 1}/{max_retries}...")
            
            import django
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
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                print(f"✅ Database connection successful! Result: {result}")
                
                # Test a more complex query (only for PostgreSQL)
                if db_config['ENGINE'] == 'django.db.backends.postgresql':
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()[0]
                    print(f"📊 PostgreSQL Version: {version}")
                else:
                    print(f"📊 Using SQLite database")
            
            return True
            
        except Exception as e:
            print(f"❌ Database connection failed (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                print(f"⏳ Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print(f"💥 All database connection attempts failed!")
                import traceback
                traceback.print_exc()
                return False

def run_migrations():
    """Run database migrations"""
    print_header("DATABASE MIGRATIONS")
    
    try:
        import django
        django.setup()
        from django.core.management import execute_from_command_line
        
        print("🔄 Running migrations...")
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
    print_header("STARTING DJANGO SERVER")
    
    try:
        import django
        django.setup()
        from django.core.management import execute_from_command_line
        
        port = os.getenv('PORT', '8000')
        host = '0.0.0.0'
        
        print(f"🌐 Starting server on {host}:{port}")
        print(f"🔗 Health check URL: http://{host}:{port}/api/health/")
        print(f"🔗 Simple health check: http://{host}:{port}/api/health/simple/")
        
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

def main():
    """Main startup function"""
    print("🚀 Chicken House Management - Railway Startup")
    print("=" * 60)
    
    # Check environment
    check_environment()
    
    # Test database connection
    if not test_database_connection():
        print("\n💥 Database connection failed. Exiting.")
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        print("\n💥 Migrations failed. Exiting.")
        sys.exit(1)
    
    # Start server
    print("\n🎉 All checks passed! Starting server...")
    start_server()

if __name__ == "__main__":
    main()
