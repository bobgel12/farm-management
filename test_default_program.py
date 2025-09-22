#!/usr/bin/env python
"""
Test script to check default program creation
"""
import os
import sys
import django
import requests
import json

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chicken_management.settings')
django.setup()

def test_default_program_api():
    """Test the default program API endpoints"""
    base_url = "http://localhost:8000/api"
    
    print("🔍 Testing default program API...")
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/health/default-program/")
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Default program exists: {data.get('default_program_exists', False)}")
            if data.get('default_program_exists'):
                print(f"Program: {data.get('program_name')} (ID: {data.get('program_id')})")
                print(f"Tasks: {data.get('total_tasks')}")
        else:
            print(f"Health check failed: {response.text}")
    except Exception as e:
        print(f"Health check error: {e}")
    
    # Test default program endpoint
    try:
        response = requests.get(f"{base_url}/programs/default/")
        print(f"\nDefault program endpoint status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Program: {data.get('name')} (ID: {data.get('id')})")
            print(f"Tasks: {data.get('total_tasks')}")
        else:
            print(f"Default program not found: {response.text}")
    except Exception as e:
        print(f"Default program endpoint error: {e}")
    
    # Test ensure default program endpoint
    try:
        response = requests.post(f"{base_url}/programs/ensure-default/")
        print(f"\nEnsure default program status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Message: {data.get('message')}")
            if 'program' in data:
                program = data['program']
                print(f"Program: {program.get('name')} (ID: {program.get('id')})")
                print(f"Tasks: {program.get('total_tasks')}")
        else:
            print(f"Ensure default program failed: {response.text}")
    except Exception as e:
        print(f"Ensure default program error: {e}")

def test_database_directly():
    """Test database directly"""
    print("\n🔍 Testing database directly...")
    
    try:
        from farms.models import Program, ProgramTask
        
        # Check all programs
        programs = Program.objects.all()
        print(f"Total programs in database: {programs.count()}")
        
        for program in programs:
            print(f"  - {program.name} (default: {program.is_default}, active: {program.is_active})")
            print(f"    Tasks: {program.tasks.count()}")
        
        # Check default programs specifically
        default_programs = Program.objects.filter(is_default=True, is_active=True)
        print(f"\nDefault active programs: {default_programs.count()}")
        
        if default_programs.exists():
            program = default_programs.first()
            print(f"Default program: {program.name} (ID: {program.id})")
            print(f"Tasks: {program.tasks.count()}")
            
            # Show some tasks
            tasks = program.tasks.all()[:5]
            print("Sample tasks:")
            for task in tasks:
                print(f"  - Day {task.day}: {task.title} ({task.task_type})")
        else:
            print("No default program found!")
            
    except Exception as e:
        print(f"Database test error: {e}")

if __name__ == '__main__':
    print("🐔 Testing Default Program Creation")
    print("=" * 50)
    
    test_database_directly()
    test_default_program_api()
    
    print("\n" + "=" * 50)
    print("Test completed!")
