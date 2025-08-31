#!/usr/bin/env python3
"""
Тестовый файл для проверки auth роутера
"""

import requests
import json

def test_auth_endpoints():
    base_url = "http://localhost:8000"
    
    print("🧪 Тестирование auth endpoints...")
    
    # Тест health endpoint
    try:
        response = requests.get(f"{base_url}/auth/health")
        print(f"✅ Health endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    # Тест login endpoint с правильными данными
    try:
        login_data = {"login": "Alexander", "password": "123"}
        response = requests.post(
            f"{base_url}/auth/superadmin/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Login endpoint (correct): {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Login endpoint error: {e}")
    
    # Тест login endpoint с неправильными данными
    try:
        login_data = {"login": "WrongUser", "password": "WrongPass"}
        response = requests.post(
            f"{base_url}/auth/superadmin/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Login endpoint (incorrect): {response.status_code}")
        if response.status_code == 401:
            print(f"   Expected error: {response.json()}")
        else:
            print(f"   Unexpected response: {response.text}")
    except Exception as e:
        print(f"❌ Login endpoint error: {e}")

if __name__ == "__main__":
    test_auth_endpoints()
