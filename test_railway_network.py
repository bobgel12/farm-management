#!/usr/bin/env python3
"""
Test Railway network connectivity for email
"""
import socket
import ssl
import smtplib
import os
from email.mime.text import MIMEText

def test_smtp_connectivity():
    """Test SMTP connectivity from Railway"""
    print("🔍 Testing Railway SMTP Connectivity")
    print("=" * 50)
    
    # Test basic network connectivity
    print("1. Testing basic network connectivity...")
    try:
        # Test DNS resolution
        socket.gethostbyname('smtp.gmail.com')
        print("✅ DNS resolution successful")
    except Exception as e:
        print(f"❌ DNS resolution failed: {e}")
        return False
    
    # Test SMTP port connectivity
    print("2. Testing SMTP port connectivity...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex(('smtp.gmail.com', 587))
        sock.close()
        
        if result == 0:
            print("✅ SMTP port 587 is reachable")
        else:
            print(f"❌ SMTP port 587 is not reachable: {result}")
            return False
    except Exception as e:
        print(f"❌ SMTP port test failed: {e}")
        return False
    
    # Test SMTP connection
    print("3. Testing SMTP connection...")
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        print("✅ SMTP connection established")
        server.quit()
        return True
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False

def test_email_config():
    """Test email configuration"""
    print("\n📧 Testing Email Configuration")
    print("=" * 50)
    
    email_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    email_port = int(os.getenv('EMAIL_PORT', '587'))
    email_user = os.getenv('EMAIL_HOST_USER', '')
    email_password = os.getenv('EMAIL_HOST_PASSWORD', '')
    
    print(f"Host: {email_host}")
    print(f"Port: {email_port}")
    print(f"User: {email_user}")
    print(f"Password: {'*' * len(email_password) if email_password else 'Not set'}")
    
    if not email_user or not email_password:
        print("❌ Email credentials not set")
        return False
    
    print("✅ Email configuration looks good")
    return True

if __name__ == "__main__":
    print("🚀 Railway Network Connectivity Test")
    print("=" * 50)
    
    # Test email config
    config_ok = test_email_config()
    
    # Test network connectivity
    network_ok = test_smtp_connectivity()
    
    print("\n📋 Results:")
    print(f"Email Config: {'✅ OK' if config_ok else '❌ FAIL'}")
    print(f"Network: {'✅ OK' if network_ok else '❌ FAIL'}")
    
    if config_ok and network_ok:
        print("\n🎉 All tests passed! Email should work.")
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")
