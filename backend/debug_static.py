#!/usr/bin/env python3
"""
Debug script to check static files configuration
"""
import os
import sys
from pathlib import Path

# Add the current directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chicken_management.settings_prod')

def debug_static_files():
    """Debug static files configuration"""
    print("🔍 Debugging Static Files Configuration")
    print("=" * 50)
    
    try:
        import django
        django.setup()
        
        from django.conf import settings
        from django.contrib.staticfiles import finders
        
        print(f"📁 STATIC_URL: {settings.STATIC_URL}")
        print(f"📁 STATIC_ROOT: {settings.STATIC_ROOT}")
        print(f"📁 STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
        
        # Check if static files exist
        static_root = Path(settings.STATIC_ROOT)
        if static_root.exists():
            print(f"✅ STATIC_ROOT exists: {static_root}")
            print(f"📂 Contents of STATIC_ROOT:")
            for item in static_root.iterdir():
                print(f"   - {item.name}")
        else:
            print(f"❌ STATIC_ROOT does not exist: {static_root}")
        
        # Check static files directories
        for static_dir in settings.STATICFILES_DIRS:
            static_path = Path(static_dir)
            if static_path.exists():
                print(f"✅ STATICFILES_DIR exists: {static_path}")
                print(f"📂 Contents of {static_path}:")
                for item in static_path.iterdir():
                    print(f"   - {item.name}")
            else:
                print(f"❌ STATICFILES_DIR does not exist: {static_path}")
        
        # Test finding a specific file
        test_file = 'js/main.js'
        found_path = finders.find(test_file)
        if found_path:
            print(f"✅ Found {test_file} at: {found_path}")
        else:
            print(f"❌ Could not find {test_file}")
            
        # List all static files
        print(f"\n📋 All static files found:")
        for finder in finders.get_finders():
            for path, storage in finder.list([]):
                print(f"   - {path}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_static_files()
