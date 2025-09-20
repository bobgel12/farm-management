#!/usr/bin/env python3
"""
Script to check Railway PostgreSQL database connection
Run this locally to verify your Railway database configuration
"""
import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chicken_management.settings_prod')

def check_environment_variables():
    """Check if required environment variables are set"""
    print("🔍 Checking Environment Variables...")
    print("=" * 50)
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print(f"✅ DATABASE_URL is set: {database_url[:30]}...")
        
        # Parse the DATABASE_URL to show details
        if 'postgres://' in database_url or 'postgresql://' in database_url:
            print("✅ Database type: PostgreSQL")
            
            # Extract components
            if '@' in database_url:
                parts = database_url.split('@')
                if len(parts) == 2:
                    user_pass = parts[0].split('://')[-1]
                    host_port_db = parts[1]
                    
                    if ':' in user_pass:
                        user, password = user_pass.split(':', 1)
                        print(f"📊 User: {user}")
                        print(f"📊 Password: {'*' * len(password)}")
                    
                    if '/' in host_port_db:
                        host_port, db_name = host_port_db.split('/', 1)
                        if ':' in host_port:
                            host, port = host_port.split(':')
                            print(f"📊 Host: {host}")
                            print(f"📊 Port: {port}")
                        else:
                            print(f"📊 Host: {host_port}")
                        print(f"📊 Database: {db_name}")
        else:
            print("⚠️  Database type: Unknown")
    else:
        print("❌ DATABASE_URL is not set")
        print("   Make sure you have a PostgreSQL service connected to your Railway project")
        return False
    
    # Check other important variables
    secret_key = os.getenv('SECRET_KEY')
    if secret_key:
        print(f"✅ SECRET_KEY is set")
    else:
        print("❌ SECRET_KEY is not set")
    
    return True

def test_database_connection():
    """Test database connection"""
    print("\n🔍 Testing Database Connection...")
    print("=" * 50)
    
    try:
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
            
            # Get PostgreSQL version
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"📊 PostgreSQL Version: {version}")
            
            # Test if we can create a table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS railway_connection_test (
                    id SERIAL PRIMARY KEY,
                    test_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert test data
            cursor.execute("""
                INSERT INTO railway_connection_test (test_message) 
                VALUES ('Railway PostgreSQL connection test successful!')
            """)
            
            # Query test data
            cursor.execute("""
                SELECT * FROM railway_connection_test 
                ORDER BY created_at DESC LIMIT 1
            """)
            result = cursor.fetchone()
            
            if result:
                print(f"✅ Database read/write test successful!")
                print(f"📊 Test data: {result[1]}")
            
            # Clean up test table
            cursor.execute("DROP TABLE IF EXISTS railway_connection_test")
            
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_django_setup():
    """Test Django setup"""
    print("\n🔍 Testing Django Setup...")
    print("=" * 50)
    
    try:
        from django.conf import settings
        print(f"✅ Django settings loaded: {settings.SETTINGS_MODULE}")
        
        from django.db import connection
        print(f"✅ Database connection available: {connection.vendor}")
        
        # Test if we can run a simple management command
        from django.core.management import execute_from_command_line
        print("✅ Django management commands available")
        
        return True
        
    except Exception as e:
        print(f"❌ Django setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Railway PostgreSQL Database Checker")
    print("=" * 60)
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    if not env_ok:
        print("\n💥 Missing DATABASE_URL environment variable.")
        print("   To fix this:")
        print("   1. Go to your Railway project dashboard")
        print("   2. Add a PostgreSQL service")
        print("   3. Connect it to your application")
        print("   4. The DATABASE_URL will be automatically set")
        sys.exit(1)
    
    # Test Django setup
    django_ok = test_django_setup()
    if not django_ok:
        print("\n💥 Django setup failed.")
        sys.exit(1)
    
    # Test database connection
    db_ok = test_database_connection()
    
    if db_ok:
        print("\n🎉 All checks passed! Your Railway PostgreSQL setup is working correctly.")
        print("\n📋 Next steps:")
        print("   1. Commit and push these changes")
        print("   2. Deploy on Railway")
        print("   3. Check the deployment logs for the startup process")
        sys.exit(0)
    else:
        print("\n💥 Database connection failed.")
        print("\n🔧 Troubleshooting steps:")
        print("   1. Verify your PostgreSQL service is running on Railway")
        print("   2. Check that the service is connected to your application")
        print("   3. Verify the DATABASE_URL environment variable is correct")
        print("   4. Check Railway logs for any database connection errors")
        sys.exit(1)