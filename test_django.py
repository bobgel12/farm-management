#!/usr/bin/env python3
"""
Simple Django test script for Railway debugging
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chicken_management.settings_prod')

def test_django_setup():
    """Test basic Django setup"""
    print("🔍 Testing Django Setup...")
    print("=" * 50)
    
    try:
        import django
        print("✅ Django import successful")
        
        django.setup()
        print("✅ Django setup successful")
        
        from django.conf import settings
        print(f"✅ Settings loaded: {settings.SETTINGS_MODULE}")
        
        from django.db import connection
        print(f"✅ Database connection available: {connection.vendor}")
        
        # Test a simple database query
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ Database query successful: {result}")
        
        print("\n🎉 Django setup test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Django setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Django Setup Test for Railway")
    print("=" * 60)
    
    success = test_django_setup()
    
    if success:
        print("\n✅ All tests passed! Django should work on Railway.")
        sys.exit(0)
    else:
        print("\n❌ Tests failed! Check the errors above.")
        sys.exit(1)
