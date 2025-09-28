#!/usr/bin/env python3
"""
POC: Rotem Web Scraper with Login Functionality
This script demonstrates web scraping the RotemNetWeb platform with authentication.
"""

import requests
import json
import sys
import time
from typing import Dict, Any, Optional
import argparse
from urllib.parse import urljoin


class RotemScraper:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.base_url = "https://rotemnetweb.com"
        self.user_token = None
        self.farm_connection_token = None
        self.session_id = None
        
        # Set up common headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://rotemnetweb.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'userLanguage': 'ENGLISH'
        })

    def login(self) -> bool:
        """
        Authenticate with the RotemNetWeb platform
        Returns True if successful, False otherwise
        """
        print("🔐 Attempting to login...")
        
        login_url = f"{self.base_url}/Latest/Services/AllServices.svc/Login"
        
        # Update headers for login request
        login_headers = self.session.headers.copy()
        login_headers.update({
            'Referer': f'{self.base_url}/Latest/rotemWebApp/User.html',
            'userToken': 'null'
        })
        
        login_data = {
            "prmUsername": self.username,
            "prmPassword": self.password,
            "prmIsNativeAppLogin": False,
            "prmIsKeepMeSignedIn": False
        }
        
        try:
            response = self.session.post(
                login_url,
                headers=login_headers,
                json=login_data,
                timeout=30
            )
            
            if response.status_code == 200:
                # Handle different encodings
                try:
                    result = response.json()
                except (UnicodeDecodeError, ValueError) as e:
                    # Try with utf-8-sig encoding for BOM issues
                    if "BOM" in str(e) or "utf-8-sig" in str(e):
                        response.encoding = 'utf-8-sig'
                        result = response.json()
                    else:
                        print(f"⚠️ JSON decode error: {e}")
                        print(f"Response text: {response.text[:200]}...")
                        return False
                
                print(f"✅ Login response: {result}")
                
                # Extract tokens from response if available
                if 'reponseObj' in result and isinstance(result['reponseObj'], dict):
                    response_data = result['reponseObj']
                    if 'FarmUser' in response_data and 'UserToken' in response_data['FarmUser']:
                        self.user_token = response_data['FarmUser']['UserToken']
                        print(f"🔑 User token extracted: {self.user_token[:50]}...")
                    
                    if 'FarmConnectionInfo' in response_data and 'ConnectionToken' in response_data['FarmConnectionInfo']:
                        self.farm_connection_token = response_data['FarmConnectionInfo']['ConnectionToken']
                        print(f"🏭 Farm connection token extracted: {self.farm_connection_token}")
                        
                    if 'FarmConnectionInfo' in response_data and 'GatewayName' in response_data['FarmConnectionInfo']:
                        self.gateway_code = response_data['FarmConnectionInfo']['GatewayName']
                        print(f"🏭 Gateway code extracted: {self.gateway_code}")
                
                # Extract session ID from cookies
                for cookie in self.session.cookies:
                    if cookie.name == 'ASP.NET_SessionId':
                        self.session_id = cookie.value
                        print(f"🍪 Session ID: {self.session_id}")
                
                return True
            else:
                print(f"❌ Login failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False

    def get_js_globals(self) -> Optional[Dict[Any, Any]]:
        """
        Get JavaScript globals configuration
        """
        print("📊 Fetching JS Globals...")
        
        url = f"{self.base_url}/Host3_V1/Services/AllServices.svc/JsGlobals_GetJsGlobals"
        
        headers = self.session.headers.copy()
        headers.update({
            'Referer': f'{self.base_url}/Host3_V1/rotemWebApp/Main.html',
            'X-Requested-With': 'XMLHttpRequest',
            'userToken': self.user_token or 'null',
            'farmConnectionToken': self.farm_connection_token or '',
            'authorization': ''
        })
        
        try:
            response = self.session.post(url, headers=headers, json={}, timeout=30)
            if response.status_code == 200:
                try:
                    result = response.json()
                except (UnicodeDecodeError, ValueError) as e:
                    # Try with utf-8-sig encoding for BOM issues
                    if "BOM" in str(e) or "utf-8-sig" in str(e):
                        response.encoding = 'utf-8-sig'
                        result = response.json()
                    else:
                        print(f"⚠️ JSON decode error: {e}")
                        print(f"Response text: {response.text[:200]}...")
                        return None
                print(f"✅ JS Globals retrieved successfully")
                return result
            else:
                print(f"❌ Failed to get JS Globals: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                return None
        except Exception as e:
            print(f"❌ Error getting JS Globals: {str(e)}")
            return None

    def get_site_controllers_info(self) -> Optional[Dict[Any, Any]]:
        """
        Get site controllers information
        """
        print("🏭 Fetching Site Controllers Info...")
        
        url = f"{self.base_url}/Host3_V1/Services/AllServices.svc/GetSiteControllersInfo"
        
        headers = self.session.headers.copy()
        headers.update({
            'Referer': f'{self.base_url}/Host3_V1/rotemWebApp/Main.html',
            'X-Requested-With': 'XMLHttpRequest',
            'userToken': self.user_token or 'null',
            'farmConnectionToken': self.farm_connection_token or '',
            'authorization': ''
        })
        
        try:
            # GetSiteControllersInfo needs specific parameters
            # Use the gateway code from the login response
            gateway_code = "tace01000155"  # Default gateway code
            if hasattr(self, 'gateway_code') and self.gateway_code:
                gateway_code = self.gateway_code
                
            request_data = {
                "prmSiteControllersInfoParams": {
                    "GatewayCode": gateway_code
                }
            }
            response = self.session.post(url, headers=headers, json=request_data, timeout=30)
            if response.status_code == 200:
                try:
                    result = response.json()
                except (UnicodeDecodeError, ValueError) as e:
                    # Try with utf-8-sig encoding for BOM issues
                    if "BOM" in str(e) or "utf-8-sig" in str(e):
                        response.encoding = 'utf-8-sig'
                        result = response.json()
                    else:
                        print(f"⚠️ JSON decode error: {e}")
                        print(f"Response text: {response.text[:200]}...")
                        return None
                print(f"✅ Site Controllers Info retrieved successfully")
                return result
            else:
                print(f"❌ Failed to get Site Controllers Info: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                return None
        except Exception as e:
            print(f"❌ Error getting Site Controllers Info: {str(e)}")
            return None

    def get_comparison_display_fields(self) -> Optional[Dict[Any, Any]]:
        """
        Get comparison display fields
        """
        print("📋 Fetching Comparison Display Fields...")
        
        url = f"{self.base_url}/Host3_V1/Services/AllServices.svc/GetComparisonDisplayFields"
        
        headers = self.session.headers.copy()
        headers.update({
            'Referer': f'{self.base_url}/Host3_V1/rotemWebApp/Main.html',
            'X-Requested-With': 'XMLHttpRequest',
            'userToken': self.user_token or 'null',
            'farmConnectionToken': self.farm_connection_token or '',
            'authorization': ''
        })
        
        try:
            response = self.session.post(url, headers=headers, json={}, timeout=30)
            if response.status_code == 200:
                try:
                    result = response.json()
                except (UnicodeDecodeError, ValueError) as e:
                    # Try with utf-8-sig encoding for BOM issues
                    if "BOM" in str(e) or "utf-8-sig" in str(e):
                        response.encoding = 'utf-8-sig'
                        result = response.json()
                    else:
                        print(f"⚠️ JSON decode error: {e}")
                        print(f"Response text: {response.text[:200]}...")
                        return None
                print(f"✅ Comparison Display Fields retrieved successfully")
                return result
            else:
                print(f"❌ Failed to get Comparison Display Fields: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                return None
        except Exception as e:
            print(f"❌ Error getting Comparison Display Fields: {str(e)}")
            return None

    def get_farm_registration(self) -> Optional[Dict[Any, Any]]:
        """
        Get farm registration information
        """
        print("🚜 Fetching Farm Registration...")
        
        url = f"{self.base_url}/Host3_V1/Services/AllServices.svc/GetFarmRegistration"
        
        headers = self.session.headers.copy()
        headers.update({
            'Referer': f'{self.base_url}/Host3_V1/rotemWebApp/Main.html',
            'X-Requested-With': 'XMLHttpRequest',
            'userToken': self.user_token or 'null',
            'farmConnectionToken': self.farm_connection_token or '',
            'authorization': ''
        })
        
        try:
            response = self.session.post(url, headers=headers, json={}, timeout=30)
            if response.status_code == 200:
                try:
                    result = response.json()
                except (UnicodeDecodeError, ValueError) as e:
                    # Try with utf-8-sig encoding for BOM issues
                    if "BOM" in str(e) or "utf-8-sig" in str(e):
                        response.encoding = 'utf-8-sig'
                        result = response.json()
                    else:
                        print(f"⚠️ JSON decode error: {e}")
                        print(f"Response text: {response.text[:200]}...")
                        return None
                print(f"✅ Farm Registration retrieved successfully")
                return result
            else:
                print(f"❌ Failed to get Farm Registration: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                return None
        except Exception as e:
            print(f"❌ Error getting Farm Registration: {str(e)}")
            return None

    def scrape_all_data(self) -> Dict[str, Any]:
        """
        Scrape all available data from the platform
        """
        print("🚀 Starting comprehensive data scraping...")
        
        all_data = {
            'login_success': False,
            'js_globals': None,
            'site_controllers_info': None,
            'comparison_display_fields': None,
            'farm_registration': None,
            'scrape_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'errors': []
        }
        
        # Attempt login first
        if not self.login():
            all_data['errors'].append("Login failed")
            return all_data
        
        all_data['login_success'] = True
        
        # Fetch all available data
        all_data['js_globals'] = self.get_js_globals()
        time.sleep(1)  # Rate limiting
        
        all_data['site_controllers_info'] = self.get_site_controllers_info()
        time.sleep(1)
        
        all_data['comparison_display_fields'] = self.get_comparison_display_fields()
        time.sleep(1)
        
        all_data['farm_registration'] = self.get_farm_registration()
        time.sleep(1)
        
        # Fetch command data for each house (1-8) to get real sensor data
        for house_num in range(1, 9):
            command_data = self.get_command_data(house_num)
            if command_data:
                all_data[f'command_data_house_{house_num}'] = command_data
            time.sleep(0.5)  # Rate limiting between houses
        
        print("✅ Data scraping completed!")
        return all_data

    def save_data(self, data: Dict[str, Any], filename: str = None) -> str:
        """
        Save scraped data to JSON file
        """
        if filename is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"rotem_scraped_data_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 Data saved to: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Error saving data: {str(e)}")
            return ""

    def print_summary(self, data: Dict[str, Any]):
        """
        Print a summary of scraped data
        """
        print("\n" + "="*50)
        print("📊 SCRAPING SUMMARY")
        print("="*50)
        print(f"Login Success: {'✅' if data['login_success'] else '❌'}")
        print(f"JS Globals: {'✅' if data['js_globals'] else '❌'}")
        print(f"Site Controllers: {'✅' if data['site_controllers_info'] else '❌'}")
        print(f"Comparison Fields: {'✅' if data['comparison_display_fields'] else '❌'}")
        print(f"Farm Registration: {'✅' if data['farm_registration'] else '❌'}")
        print(f"Scrape Time: {data['scrape_timestamp']}")
        
        if data['errors']:
            print(f"Errors: {len(data['errors'])}")
            for error in data['errors']:
                print(f"  - {error}")
        
        print("="*50)

    def get_command_data(self, house_number: int = 2) -> Optional[Dict[Any, Any]]:
        """
        Get detailed command data for a specific house
        This endpoint returns real sensor data with actual values
        """
        print(f"🏠 Fetching Command Data for House {house_number}...")
        
        url = f"{self.base_url}/Host3_V1/Services/AllServices.svc/RNBL_GetCommandData"
        
        headers = self.session.headers.copy()
        headers.update({
            'Referer': f'{self.base_url}/Host3_V1/Main.html',
            'X-Requested-With': 'XMLHttpRequest',
            'userToken': self.user_token or 'null',
            'farmConnectionToken': self.farm_connection_token or '',
            'authorization': '',
            'userLanguage': 'ENGLISH'
        })
        
        try:
            request_data = {
                "prmGetCommandDataParams": {
                    "CommandID": "0",
                    "IsSetPointCommand": False,
                    "HouseNumber": str(house_number),
                    "RoomNumber": -1,
                    "ClientLanguageIndex": 1,
                    "IsIgnoreCache": False,
                    "PageNumber": -1,
                    "IsLoadPageFromCache": False
                }
            }
            
            response = self.session.post(url, headers=headers, json=request_data, timeout=30)
            if response.status_code == 200:
                try:
                    result = response.json()
                except (UnicodeDecodeError, ValueError) as e:
                    # Try with utf-8-sig encoding for BOM issues
                    if "BOM" in str(e) or "utf-8-sig" in str(e):
                        response.encoding = 'utf-8-sig'
                        result = response.json()
                    else:
                        print(f"⚠️ JSON decode error: {e}")
                        print(f"Response text: {response.text[:200]}...")
                        return None
                print(f"✅ Command data for house {house_number} retrieved successfully")
                return result
            else:
                print(f"❌ Failed to get Command Data for house {house_number}: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                return None
        except Exception as e:
            print(f"❌ Error getting Command Data for house {house_number}: {str(e)}")
            return None


def main():
    parser = argparse.ArgumentParser(description='Rotem Web Scraper POC')
    parser.add_argument('username', help='Username/Email for login')
    parser.add_argument('password', help='Password for login')
    parser.add_argument('--output', '-o', help='Output filename for scraped data')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    print("🌐 Rotem Web Scraper POC")
    print("="*30)
    
    # Create scraper instance
    scraper = RotemScraper(args.username, args.password)
    
    # Scrape all data
    data = scraper.scrape_all_data()
    
    # Print summary
    scraper.print_summary(data)
    
    # Save data
    if data['login_success']:
        output_file = scraper.save_data(data, args.output)
        if output_file:
            print(f"\n🎉 Scraping completed successfully!")
            print(f"📁 Data saved to: {output_file}")
    else:
        print("\n❌ Scraping failed due to login issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
