#!/usr/bin/env python3
"""
Test script for new feature API endpoints
Tests organizations, flocks, analytics, and reporting APIs
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8002/api"
TOKEN = "ea4e6854f8eb3e3491e98cf164e5d5abd95fe5ea"  # Admin token

headers = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json"
}

def test_endpoint(name, url, method="GET", data=None):
    """Test an API endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            try:
                result = response.json()
                print(f"✅ Success!")
                print(f"Response: {json.dumps(result, indent=2)}")
                return True
            except json.JSONDecodeError:
                print(f"✅ Success! (No JSON response)")
                print(f"Response: {response.text[:200]}")
                return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            try:
                error = response.json()
                print(f"Error: {json.dumps(error, indent=2)}")
            except:
                print(f"Error: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error - Is the server running on {BASE_URL}?")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Run all API tests"""
    print("🧪 Testing New Feature API Endpoints")
    print("="*60)
    
    results = []
    
    # Test Organizations
    results.append(("Organizations List", test_endpoint(
        "Organizations List",
        f"{BASE_URL}/organizations/"
    )))
    
    results.append(("My Organizations", test_endpoint(
        "My Organizations",
        f"{BASE_URL}/organizations/my-organizations/"
    )))
    
    # Test Breeds
    results.append(("Breeds List", test_endpoint(
        "Breeds List",
        f"{BASE_URL}/breeds/"
    )))
    
    # Test Flocks
    results.append(("Flocks List", test_endpoint(
        "Flocks List",
        f"{BASE_URL}/flocks/"
    )))
    
    # Test Analytics
    results.append(("KPIs List", test_endpoint(
        "KPIs List",
        f"{BASE_URL}/kpis/"
    )))
    
    results.append(("Dashboards List", test_endpoint(
        "Dashboards List",
        f"{BASE_URL}/dashboards/"
    )))
    
    results.append(("Benchmarks List", test_endpoint(
        "Benchmarks List",
        f"{BASE_URL}/benchmarks/"
    )))
    
    # Test Reporting
    results.append(("Report Templates List", test_endpoint(
        "Report Templates List",
        f"{BASE_URL}/report-templates/"
    )))
    
    results.append(("Scheduled Reports List", test_endpoint(
        "Scheduled Reports List",
        f"{BASE_URL}/scheduled-reports/"
    )))
    
    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All API endpoints are working correctly!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

