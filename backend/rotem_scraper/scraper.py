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
import shlex


class RotemScraper:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.base_url = "https://rotemnetweb.com"
        self.user_token = None
        self.farm_connection_token = None
        self.session_id = None
        self.last_error_message = None
        self.web_server_url = f"{self.base_url}/Host3_V1/"
        
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

    def _service_url(self, endpoint: str) -> str:
        """Build service URL from login-resolved web server URL."""
        base = (self.web_server_url or f"{self.base_url}/Host3_V1/").rstrip('/')
        return f"{base}/Services/AllServices.svc/{endpoint}"

    def _referer_url(self, page: str = "Main.html") -> str:
        """Build referer URL from login-resolved web server URL."""
        base = (self.web_server_url or f"{self.base_url}/Host3_V1/").rstrip('/')
        if page.startswith("rotemWebApp/"):
            return f"{base}/{page}"
        return f"{base}/rotemWebApp/{page}"

    def _normalize_web_server_url(self, value: str) -> str:
        """Normalize WebServerUrl values to absolute URL with trailing slash."""
        if not value:
            return value
        url = value.strip()
        if url.startswith('/'):
            url = f"{self.base_url}{url}"
        if not url.startswith('http'):
            url = f"{self.base_url}/{url.lstrip('/')}"
        if not url.endswith('/'):
            url = f"{url}/"
        return url

    def _extract_web_server_url(self, result: Dict[str, Any]) -> Optional[str]:
        """Extract WebServerUrl from known login payload shapes."""
        if not isinstance(result, dict):
            return None

        candidate_containers = [
            result,
            result.get('reponseObj'),
            result.get('responseObj'),
        ]

        # Also inspect common nested containers if present.
        response_obj = result.get('reponseObj') or result.get('responseObj')
        if isinstance(response_obj, dict):
            candidate_containers.extend([
                response_obj.get('FarmUser'),
                response_obj.get('FarmConnectionInfo'),
            ])

        for container in candidate_containers:
            if not isinstance(container, dict):
                continue
            for key in ('WebServerUrl', 'webServerUrl', 'web_server_url'):
                value = container.get(key)
                if isinstance(value, str) and value.strip():
                    return self._normalize_web_server_url(value)

        return None

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
                self.last_error_message = None

                # Rotem may return HTTP 200 with logical failure in payload
                if isinstance(result, dict) and result.get('isSucceed') is False:
                    error_message = (
                        result.get('exceptionMessage')
                        or result.get('ErrorObj')
                        or result.get('errorObj')
                        or "Login payload indicates failure"
                    )
                    self.last_error_message = str(error_message)
                    print(f"❌ Login rejected by payload: {self.last_error_message}")
                    return False
                
                # Extract tokens from response if available
                response_data = None
                if isinstance(result, dict):
                    response_data = result.get('reponseObj') or result.get('responseObj')

                web_server_url = self._extract_web_server_url(result)
                if web_server_url:
                    self.web_server_url = web_server_url
                    print(f"🌐 Web server URL from login: {self.web_server_url}")
                else:
                    print(f"🌐 Web server URL not found in login payload, keeping: {self.web_server_url}")

                if isinstance(response_data, dict):
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
                print(f"🌐 Effective web_server_url after login: {self.web_server_url}")

                # Missing tokens usually means account has no farm access context
                if not self.user_token or not self.farm_connection_token:
                    self.last_error_message = (
                        "Login succeeded but missing user_token or farm_connection_token. "
                        "Account may not have farm access/selection context."
                    )
                    print(f"❌ {self.last_error_message}")
                    return False
                
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
        
        url = self._service_url("JsGlobals_GetJsGlobals")
        
        headers = self.session.headers.copy()
        headers.update({
            'Referer': self._referer_url("Main.html"),
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
        
        url = self._service_url("GetSiteControllersInfo")
        
        headers = self.session.headers.copy()
        headers.update({
            'Referer': self._referer_url("Main.html"),
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
        
        url = self._service_url("GetComparisonDisplayFields")
        
        headers = self.session.headers.copy()
        headers.update({
            'Referer': self._referer_url("Main.html"),
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
        
        url = self._service_url("GetFarmRegistration")
        
        headers = self.session.headers.copy()
        headers.update({
            'Referer': self._referer_url("Main.html"),
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

    def get_command_data(self, house_number: int = 2, command_id: str = "0", _retried: bool = False) -> Optional[Dict[Any, Any]]:
        """
        Get detailed command data for a specific house
        This endpoint returns real sensor data with actual values
        command_id: "0" = General, "40" = Water History
        """
        print(f"🏠 Fetching Command Data for House {house_number}, CommandID: {command_id}...")
        print(f"🌐 Active web_server_url: {self.web_server_url}")
        
        url = self._service_url("RNBL_GetCommandData")
        
        headers = self.session.headers.copy()
        headers.update({
            'Referer': self._referer_url("Main.html"),
            'X-Requested-With': 'XMLHttpRequest',
            'userToken': self.user_token or 'null',
            'farmConnectionToken': self.farm_connection_token or '',
            'authorization': '',
            'userLanguage': 'ENGLISH'
        })
        
        try:
            request_data = {
                "prmGetCommandDataParams": {
                    "CommandID": command_id,
                    "IsSetPointCommand": False,
                    "HouseNumber": str(house_number),
                    "RoomNumber": -1,
                    "ClientLanguageIndex": 1,
                    "IsIgnoreCache": False,
                    "PageNumber": -1,
                    "IsLoadPageFromCache": False
                }
            }
            
            # Increased timeout to 60 seconds for water history data which can be large
            response = self.session.post(url, headers=headers, json=request_data, timeout=60)
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
                response_obj = None
                if isinstance(result, dict):
                    response_obj = result.get('reponseObj') or result.get('responseObj')
                    if not isinstance(response_obj, dict):
                        keys_preview = list(result.keys())
                        error_obj = result.get('ErrorObj') or result.get('errorObj')
                        exception_message = result.get('exceptionMessage')
                        is_succeed = result.get('isSucceed')
                        is_authorize = result.get('isAuthorize')
                        is_in_session = result.get('isInSession')
                        print(
                            f"⚠️ House {house_number} returned no usable response object. "
                            f"keys={keys_preview}, errorObj={error_obj}, "
                            f"exceptionMessage={exception_message}, "
                            f"isSucceed={is_succeed}, isAuthorize={is_authorize}, isInSession={is_in_session}"
                        )
                        self._log_curl_debug(url, headers, request_data, house_number, command_id)

                        # Some accounts return invalid session/authorization context after login.
                        # Re-login and retry once before failing this house request.
                        if not _retried and (is_authorize is False or is_in_session is False):
                            print(f"🔁 Re-authenticating and retrying house {house_number} command once...")
                            if self.login():
                                return self.get_command_data(
                                    house_number=house_number,
                                    command_id=command_id,
                                    _retried=True
                                )
                            self.last_error_message = (
                                "Rotem command unauthorized after re-authentication "
                                f"(house={house_number}, isAuthorize={is_authorize}, isInSession={is_in_session})"
                            )
                return result
            else:
                print(f"❌ Failed to get Command Data for house {house_number}: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                return None
        except Exception as e:
            print(f"❌ Error getting Command Data for house {house_number}: {str(e)}")
            return None

    def _log_curl_debug(
        self,
        url: str,
        headers: Dict[str, str],
        request_data: Dict[str, Any],
        house_number: int,
        command_id: str
    ) -> None:
        """
        Print a reproducible curl command for debugging failed/unauthorized requests.
        """
        allowed_headers = [
            "Referer",
            "X-Requested-With",
            "userToken",
            "farmConnectionToken",
            "authorization",
            "userLanguage",
            "Content-Type",
            "Origin",
        ]
        curl_parts = ["curl", "-X", "POST", shlex.quote(url)]
        for header_name in allowed_headers:
            if header_name in headers:
                header_value = headers[header_name]
                curl_parts.extend(["-H", shlex.quote(f"{header_name}: {header_value}")])

        payload = json.dumps(request_data, separators=(",", ":"))
        curl_parts.extend(["--data-raw", shlex.quote(payload)])

        print(
            f"🧪 Debug curl for house {house_number}, command {command_id}:\n"
            f"{' '.join(curl_parts)}"
        )

    def get_water_history(self, house_number: int, start_date: str = None, end_date: str = None) -> Optional[Dict[Any, Any]]:
        """
        Get water consumption history for a specific house from Rotem API
        Uses CommandID 40 to fetch water history data
        """
        print(f"💧 Fetching Water History for House {house_number}...")
        
        # Use CommandID 40 to get water history (this is the correct endpoint based on the curl example)
        command_data = self.get_command_data(house_number, command_id="40")
        if command_data:
            print(f"📊 RNBL_GetCommandData (CommandID: 40) response structure: {json.dumps(command_data, indent=2, default=str)[:2000]}")
            
            # Check if command_data contains water history data in dsData.Data
            if 'reponseObj' in command_data:
                response_obj = command_data['reponseObj']
                
                # Check if dsData.Data exists (this contains the water history records)
                if 'dsData' in response_obj:
                    ds_data = response_obj['dsData']
                    if 'Data' in ds_data and isinstance(ds_data['Data'], list):
                        print(f"✅ Found water history data in dsData.Data with {len(ds_data['Data'])} records")
                        return command_data
                
                # Also check for direct water history fields
                if 'WaterHistory' in response_obj:
                    return response_obj['WaterHistory']
                elif 'ConsumptionHistory' in response_obj:
                    return response_obj['ConsumptionHistory']
                elif 'History' in response_obj:
                    history = response_obj['History']
                    if 'Water' in history:
                        return history['Water']
            
            # Return the data even if structure is different (for parsing)
            return command_data
        
        print(f"❌ No water history data found from Rotem API")
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
