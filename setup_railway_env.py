#!/usr/bin/env python3
"""
Script to help set up Railway environment variables
"""
import secrets
import string

def generate_secret_key():
    """Generate a Django secret key"""
    chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(chars) for _ in range(50))

def main():
    print("🚀 Railway Environment Variables Setup")
    print("=" * 50)
    
    # Generate a secret key
    secret_key = generate_secret_key()
    
    print("📋 Required Environment Variables for Railway:")
    print("=" * 50)
    print(f"SECRET_KEY={secret_key}")
    print("DATABASE_URL=<automatically set by Railway PostgreSQL service>")
    print("DEBUG=False")
    print("ALLOWED_HOSTS=*")
    
    print("\n🔧 How to set these in Railway:")
    print("=" * 50)
    print("1. Go to your Railway project dashboard")
    print("2. Click on your application service")
    print("3. Go to the 'Variables' tab")
    print("4. Add the following variables:")
    print(f"   - SECRET_KEY: {secret_key}")
    print("   - DEBUG: False")
    print("   - ALLOWED_HOSTS: *")
    print("\n5. Make sure you have a PostgreSQL service connected")
    print("   - The DATABASE_URL will be automatically set")
    
    print("\n✅ After setting these variables:")
    print("=" * 50)
    print("1. Commit and push your code changes")
    print("2. Redeploy on Railway")
    print("3. Check the deployment logs")
    
    print(f"\n🔑 Your generated SECRET_KEY: {secret_key}")
    print("   (Copy this value to Railway's SECRET_KEY variable)")

if __name__ == "__main__":
    main()
