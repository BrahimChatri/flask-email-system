#!/usr/bin/env python3
"""
Simple API test script for Flask Gmail System
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Health check: Connection failed - server not running")
        return False

def test_register():
    """Test user registration"""
    try:
        data = {
            "username": "testuser",
            "password": "testpassword123",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=data)
        print(f"✅ Register: {response.status_code}")
        if response.status_code in [201, 400]:  # 400 if user already exists
            print(f"   Response: {response.json()}")
        return response.status_code in [201, 400]
    except requests.exceptions.ConnectionError:
        print("❌ Register: Connection failed")
        return False

def test_login():
    """Test user login"""
    try:
        data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=data)
        print(f"✅ Login: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Access token: {result.get('access_token', 'N/A')[:20]}...")
            return result.get('access_token')
        else:
            print(f"   Response: {response.json()}")
            return None
    except requests.exceptions.ConnectionError:
        print("❌ Login: Connection failed")
        return None

def test_protected_endpoint(token):
    """Test a protected endpoint"""
    if not token:
        print("❌ Protected endpoint: No token available")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"✅ Protected endpoint: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   User: {result.get('user', {}).get('username', 'N/A')}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Protected endpoint: Connection failed")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Flask Gmail System API")
    print("=" * 50)
    
    # Test health check
    if not test_health_check():
        print("\n❌ Server is not running. Please start the server first:")
        print("   python app.py")
        return
    
    print("\n" + "=" * 50)
    
    # Test registration
    test_register()
    
    print("\n" + "=" * 50)
    
    # Test login
    token = test_login()
    
    print("\n" + "=" * 50)
    
    # Test protected endpoint
    if token:
        test_protected_endpoint(token)
    
    print("\n" + "=" * 50)
    print("✅ API testing completed!")

if __name__ == "__main__":
    main()
