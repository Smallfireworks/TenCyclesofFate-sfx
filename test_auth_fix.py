#!/usr/bin/env python3
"""
Quick test to verify the authentication system fix.
This tests that the get_password_hash function is properly available.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_auth_import():
    """Test that the auth module can be imported without errors."""
    try:
        print("Testing auth_simple module import...")
        from app.auth_simple import get_password_hash, verify_password, USERS_DB
        print("✅ Successfully imported auth_simple module")
        
        # Test password hashing
        print("Testing password hashing...")
        test_password = "test123"
        hashed = get_password_hash(test_password)
        print(f"✅ Password hashed successfully: {hashed[:20]}...")
        
        # Test password verification
        print("Testing password verification...")
        if verify_password(test_password, hashed):
            print("✅ Password verification successful")
        else:
            print("❌ Password verification failed")
            return False
        
        # Test wrong password
        if not verify_password("wrong_password", hashed):
            print("✅ Wrong password correctly rejected")
        else:
            print("❌ Wrong password incorrectly accepted")
            return False
        
        # Test users database
        print("Testing users database...")
        print(f"✅ Users database loaded with {len(USERS_DB)} users")
        for username in USERS_DB.keys():
            print(f"   - {username}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing or testing auth module: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test configuration loading."""
    try:
        print("\nTesting configuration...")
        from app.config import settings
        print("✅ Configuration loaded successfully")
        
        # Check important settings
        if hasattr(settings, 'SECRET_KEY') and settings.SECRET_KEY:
            print("✅ SECRET_KEY is configured")
        else:
            print("⚠️  SECRET_KEY not configured (this is expected in test environment)")
        
        if hasattr(settings, 'AUTH_USERS'):
            print(f"✅ AUTH_USERS setting available: {bool(settings.AUTH_USERS)}")
        else:
            print("⚠️  AUTH_USERS setting not available")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Testing Authentication System Fix")
    print("=" * 50)
    
    # Set up minimal environment for testing
    os.environ.setdefault('SECRET_KEY', 'test_secret_key_for_testing_only')
    os.environ.setdefault('AUTH_USERS', 'admin:admin123,test:test123')
    
    config_ok = test_config()
    auth_ok = test_auth_import()
    
    print("\n📊 Test Results")
    print("=" * 30)
    print(f"Configuration: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"Authentication: {'✅ PASS' if auth_ok else '❌ FAIL'}")
    
    if config_ok and auth_ok:
        print("\n🎉 All tests passed! The authentication fix is working.")
        print("💡 The NameError: name 'get_password_hash' is not defined should be resolved.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
