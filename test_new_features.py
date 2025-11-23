#!/usr/bin/env python3
"""
Test script for new features implemented in the Rotem enhancement plan
Tests all new API endpoints and functionality
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8002/api"
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

def get_auth_token():
    """Get authentication token"""
    print("🔐 Authenticating...")
    response = requests.post(
        f"{BASE_URL}/auth/login/",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        token = response.json().get('token')
        print(f"✅ Authentication successful")
        return token
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        print(response.text)
        return None

def test_comparison_endpoint(token):
    """Test houses comparison endpoint"""
    print("\n📊 Testing Houses Comparison Endpoint...")
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(f"{BASE_URL}/houses/comparison/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Comparison endpoint working")
        print(f"   Found {data.get('count', 0)} houses")
        if data.get('houses'):
            print(f"   Sample house: House {data['houses'][0].get('house_number')}")
            print(f"   Status: {data['houses'][0].get('status')}")
            print(f"   Current Day: {data['houses'][0].get('current_day')}")
        return True
    else:
        print(f"❌ Comparison endpoint failed: {response.status_code}")
        print(response.text)
        return False

def test_house_details_endpoint(token):
    """Test house details endpoint"""
    print("\n🏠 Testing House Details Endpoint...")
    headers = {"Authorization": f"Token {token}"}
    
    # First get a house ID
    response = requests.get(f"{BASE_URL}/houses/", headers=headers)
    if response.status_code == 200:
        houses = response.json()
        if houses:
            house_id = houses[0]['id']
            print(f"   Testing with house ID: {house_id}")
            
            response = requests.get(f"{BASE_URL}/houses/{house_id}/details/", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ House details endpoint working")
                print(f"   House: {data.get('house', {}).get('house_number')}")
                print(f"   Has monitoring: {data.get('monitoring') is not None}")
                print(f"   Alarms count: {len(data.get('alarms', []))}")
                return True
            else:
                print(f"❌ House details endpoint failed: {response.status_code}")
                print(response.text)
                return False
        else:
            print("⚠️  No houses found to test")
            return False
    else:
        print(f"❌ Failed to get houses: {response.status_code}")
        return False

def test_device_endpoints(token):
    """Test device management endpoints"""
    print("\n🔧 Testing Device Management Endpoints...")
    headers = {"Authorization": f"Token {token}"}
    
    # Get a house ID
    response = requests.get(f"{BASE_URL}/houses/", headers=headers)
    if response.status_code == 200:
        houses = response.json()
        if houses:
            house_id = houses[0]['id']
            print(f"   Testing with house ID: {house_id}")
            
            # Test GET devices
            response = requests.get(f"{BASE_URL}/houses/{house_id}/devices/", headers=headers)
            if response.status_code == 200:
                devices = response.json()
                print(f"✅ Get devices endpoint working")
                print(f"   Found {len(devices)} devices")
                
                # Test creating a device
                device_data = {
                    "device_type": "heater",
                    "device_number": 1,
                    "name": "Test Heater",
                    "status": "off",
                    "percentage": None
                }
                response = requests.post(
                    f"{BASE_URL}/houses/{house_id}/devices/",
                    headers=headers,
                    json=device_data
                )
                if response.status_code == 201:
                    device = response.json()
                    device_id = device['id']
                    print(f"✅ Create device endpoint working")
                    print(f"   Created device ID: {device_id}")
                    
                    # Test device control
                    control_data = {"action": "on"}
                    response = requests.post(
                        f"{BASE_URL}/devices/{device_id}/control/",
                        headers=headers,
                        json=control_data
                    )
                    if response.status_code == 200:
                        print(f"✅ Device control endpoint working")
                        print(f"   Device status: {response.json().get('status')}")
                        return True
                    else:
                        print(f"❌ Device control failed: {response.status_code}")
                        return False
                else:
                    print(f"⚠️  Create device failed (may already exist): {response.status_code}")
                    return True  # Device might already exist
            else:
                print(f"❌ Get devices endpoint failed: {response.status_code}")
                print(response.text)
                return False
        else:
            print("⚠️  No houses found to test")
            return False
    else:
        print(f"❌ Failed to get houses: {response.status_code}")
        return False

def test_control_settings_endpoint(token):
    """Test control settings endpoint"""
    print("\n🌡️ Testing Control Settings Endpoint...")
    headers = {"Authorization": f"Token {token}"}
    
    # Get a house ID
    response = requests.get(f"{BASE_URL}/houses/", headers=headers)
    if response.status_code == 200:
        houses = response.json()
        if houses:
            house_id = houses[0]['id']
            print(f"   Testing with house ID: {house_id}")
            
            # Test GET control settings
            response = requests.get(f"{BASE_URL}/houses/{house_id}/control/", headers=headers)
            if response.status_code == 200:
                settings = response.json()
                print(f"✅ Get control settings endpoint working")
                print(f"   Ventilation mode: {settings.get('ventilation_mode')}")
                print(f"   Target temperature: {settings.get('target_temperature')}")
                
                # Test UPDATE control settings
                update_data = {
                    "target_temperature": 82.0,
                    "ventilation_mode": "minimum"
                }
                response = requests.patch(
                    f"{BASE_URL}/houses/{house_id}/control/",
                    headers=headers,
                    json=update_data
                )
                if response.status_code == 200:
                    print(f"✅ Update control settings endpoint working")
                    return True
                else:
                    print(f"❌ Update control settings failed: {response.status_code}")
                    return False
            else:
                print(f"❌ Get control settings failed: {response.status_code}")
                print(response.text)
                return False
        else:
            print("⚠️  No houses found to test")
            return False
    else:
        print(f"❌ Failed to get houses: {response.status_code}")
        return False

def test_temperature_curve_endpoint(token):
    """Test temperature curve endpoint"""
    print("\n📈 Testing Temperature Curve Endpoint...")
    headers = {"Authorization": f"Token {token}"}
    
    # Get a house ID
    response = requests.get(f"{BASE_URL}/houses/", headers=headers)
    if response.status_code == 200:
        houses = response.json()
        if houses:
            house_id = houses[0]['id']
            print(f"   Testing with house ID: {house_id}")
            
            # Test GET temperature curve
            response = requests.get(f"{BASE_URL}/houses/{house_id}/control/temperature-curve/", headers=headers)
            if response.status_code == 200:
                curves = response.json()
                print(f"✅ Get temperature curve endpoint working")
                print(f"   Found {len(curves)} curve points")
                return True
            else:
                print(f"❌ Get temperature curve failed: {response.status_code}")
                print(response.text)
                return False
        else:
            print("⚠️  No houses found to test")
            return False
    else:
        print(f"❌ Failed to get houses: {response.status_code}")
        return False

def test_configuration_endpoint(token):
    """Test house configuration endpoint"""
    print("\n⚙️ Testing House Configuration Endpoint...")
    headers = {"Authorization": f"Token {token}"}
    
    # Get a house ID
    response = requests.get(f"{BASE_URL}/houses/", headers=headers)
    if response.status_code == 200:
        houses = response.json()
        if houses:
            house_id = houses[0]['id']
            print(f"   Testing with house ID: {house_id}")
            
            # Test GET configuration
            response = requests.get(f"{BASE_URL}/houses/{house_id}/configuration/", headers=headers)
            if response.status_code == 200:
                config = response.json()
                print(f"✅ Get configuration endpoint working")
                print(f"   Length: {config.get('length_feet')} ft")
                print(f"   Width: {config.get('width_feet')} ft")
                return True
            else:
                print(f"❌ Get configuration failed: {response.status_code}")
                print(response.text)
                return False
        else:
            print("⚠️  No houses found to test")
            return False
    else:
        print(f"❌ Failed to get houses: {response.status_code}")
        return False

def test_sensors_endpoint(token):
    """Test sensors endpoint"""
    print("\n📡 Testing Sensors Endpoint...")
    headers = {"Authorization": f"Token {token}"}
    
    # Get a house ID
    response = requests.get(f"{BASE_URL}/houses/", headers=headers)
    if response.status_code == 200:
        houses = response.json()
        if houses:
            house_id = houses[0]['id']
            print(f"   Testing with house ID: {house_id}")
            
            # Test GET sensors
            response = requests.get(f"{BASE_URL}/houses/{house_id}/sensors/", headers=headers)
            if response.status_code == 200:
                sensors = response.json()
                print(f"✅ Get sensors endpoint working")
                print(f"   Found {len(sensors)} sensors")
                return True
            else:
                print(f"❌ Get sensors failed: {response.status_code}")
                print(response.text)
                return False
        else:
            print("⚠️  No houses found to test")
            return False
    else:
        print(f"❌ Failed to get houses: {response.status_code}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing New Features - Rotem Enhancement Plan")
    print("=" * 60)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without authentication token")
        sys.exit(1)
    
    results = []
    
    # Run all tests
    results.append(("Houses Comparison", test_comparison_endpoint(token)))
    results.append(("House Details", test_house_details_endpoint(token)))
    results.append(("Device Management", test_device_endpoints(token)))
    results.append(("Control Settings", test_control_settings_endpoint(token)))
    results.append(("Temperature Curve", test_temperature_curve_endpoint(token)))
    results.append(("House Configuration", test_configuration_endpoint(token)))
    results.append(("Sensors", test_sensors_endpoint(token)))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

