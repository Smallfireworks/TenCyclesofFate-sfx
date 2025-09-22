#!/usr/bin/env python3
"""
Simple test script to validate the authentication system.
Run this script to test the new username/password authentication.
"""

import os
import sys
import requests
import json
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_auth_system():
    """Test the authentication system."""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Authentication System")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing health check endpoint...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Cannot connect to server: {e}")
        print("   💡 Make sure the server is running with: ./run.sh")
        return False
    
    # Test 2: Login with invalid credentials
    print("2. Testing login with invalid credentials...")
    try:
        response = requests.post(
            f"{base_url}/api/login",
            data={"username": "invalid", "password": "invalid"},
            timeout=5
        )
        if response.status_code == 401:
            print("   ✅ Invalid login correctly rejected")
        else:
            print(f"   ❌ Expected 401, got {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Login test failed: {e}")
        return False
    
    # Test 3: Login with valid credentials (if available)
    print("3. Testing login with default credentials...")
    try:
        response = requests.post(
            f"{base_url}/api/login",
            data={"username": "admin", "password": "changeme123"},
            timeout=5
        )
        if response.status_code == 200:
            print("   ✅ Default login successful")
            
            # Test 4: Access protected endpoint
            print("4. Testing protected endpoint access...")
            cookies = response.cookies
            game_response = requests.post(
                f"{base_url}/api/game/init",
                cookies=cookies,
                timeout=5
            )
            if game_response.status_code == 200:
                print("   ✅ Protected endpoint accessible with valid token")
            else:
                print(f"   ❌ Protected endpoint failed: {game_response.status_code}")
        else:
            print(f"   ⚠️  Default login failed: {response.status_code}")
            print("   💡 This is expected if you changed the default credentials")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Login test failed: {e}")
        return False
    
    # Test 5: Access protected endpoint without token
    print("5. Testing protected endpoint without authentication...")
    try:
        response = requests.post(f"{base_url}/api/game/init", timeout=5)
        if response.status_code == 401:
            print("   ✅ Protected endpoint correctly requires authentication")
        else:
            print(f"   ❌ Expected 401, got {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Protected endpoint test failed: {e}")
        return False
    
    print("\n🎉 Authentication system tests completed!")
    return True

def test_config():
    """Test configuration loading."""
    print("\n🔧 Testing Configuration")
    print("=" * 50)
    
    try:
        from backend.app.config import settings
        
        print("1. Testing configuration loading...")
        print(f"   Host: {settings.HOST}")
        print(f"   Port: {settings.PORT}")
        print(f"   Algorithm: {settings.ALGORITHM}")
        
        if settings.SECRET_KEY:
            print("   ✅ SECRET_KEY is set")
        else:
            print("   ❌ SECRET_KEY is not set")
            return False
        
        if settings.AUTH_USERS:
            print("   ✅ AUTH_USERS is configured")
            # Parse users
            users = {}
            for user_pair in settings.AUTH_USERS.split(','):
                if ':' in user_pair:
                    username, password = user_pair.strip().split(':', 1)
                    users[username.strip()] = password.strip()
            print(f"   📝 Configured users: {list(users.keys())}")
        else:
            print("   ⚠️  AUTH_USERS not set, using default admin user")
        
        print("   ✅ Configuration loaded successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 浮生十梦 - System Validation Tests")
    print("=" * 60)
    
    # Test configuration first
    config_ok = test_config()
    
    # Test authentication system
    auth_ok = test_auth_system()
    
    print("\n📊 Test Summary")
    print("=" * 30)
    print(f"Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"Authentication: {'✅ PASS' if auth_ok else '❌ FAIL'}")
    
    if config_ok and auth_ok:
        print("\n🎉 All tests passed! The system is ready to use.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the configuration and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
