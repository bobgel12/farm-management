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

# Setup Django
django.setup()

from django.db import connection
from django.conf import settings

def check_database_connection():
    """Check if database connection is working"""
    print("🔍 Checking Railway PostgreSQL Database Connection...")
    print("=" * 50)
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print(f"✅ DATABASE_URL is set: {database_url[:20]}...")
    else:
        print("❌ DATABASE_URL is not set")
        print("   Make sure you have a PostgreSQL service connected to your Railway project")
        return False
    
    # Check database configuration
    db_config = settings.DATABASES['default']
    print(f"📊 Database Engine: {db_config['ENGINE']}")
    print(f"📊 Database Name: {db_config['NAME']}")
    print(f"📊 Database Host: {db_config['HOST']}")
    print(f"📊 Database Port: {db_config['PORT']}")
    
    # Test database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ Database connection successful!")
            print(f"📊 PostgreSQL Version: {version}")
            
            # Test if we can create a simple table (for testing)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS railway_test (
                    id SERIAL PRIMARY KEY,
                    test_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert test data
            cursor.execute("""
                INSERT INTO railway_test (test_data) VALUES ('Railway connection test')
            """)
            
            # Query test data
            cursor.execute("SELECT * FROM railway_test ORDER BY created_at DESC LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                print(f"✅ Database read/write test successful!")
                print(f"📊 Test data: {result[1]}")
            
            # Clean up test table
            cursor.execute("DROP TABLE IF EXISTS railway_test")
            
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def check_environment_variables():
    """Check required environment variables"""
    print("\n🔍 Checking Environment Variables...")
    print("=" * 50)
    
    required_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
    ]
    
    optional_vars = [
        'ALLOWED_HOSTS',
        'CORS_ALLOWED_ORIGINS',
        'CSRF_TRUSTED_ORIGINS',
    ]
    
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Not set (REQUIRED)")
            all_good = False
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Set")
        else:
            print(f"⚠️  {var}: Not set (optional)")
    
    return all_good

if __name__ == "__main__":
    print("🚀 Railway PostgreSQL Database Checker")
    print("=" * 50)
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    if env_ok:
        # Check database connection
        db_ok = check_database_connection()
        
        if db_ok:
            print("\n🎉 All checks passed! Your Railway PostgreSQL setup is working correctly.")
            sys.exit(0)
        else:
            print("\n💥 Database connection failed. Check your Railway PostgreSQL service.")
            sys.exit(1)
    else:
        print("\n💥 Missing required environment variables.")
        print("   Make sure to set up your Railway environment variables properly.")
        sys.exit(1)
