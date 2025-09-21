#!/usr/bin/env python3
"""
Тест клиентских API endpoints
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8080"

def test_sms_send():
    """Тест отправки SMS"""
    print("🧪 Тестируем отправку SMS...")
    
    url = f"{BASE_URL}/api/sms/send"
    data = {
        "phoneNumber": "+9961111111111"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"📱 SMS Send - Status: {response.status_code}")
        print(f"📱 SMS Send - Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ SMS Send Error: {e}")
        return False

def test_client_login():
    """Тест авторизации клиента"""
    print("🧪 Тестируем авторизацию клиента...")
    
    url = f"{BASE_URL}/api/clients/login"
    data = {
        "phone_number": "+9961111111111",
        "sms_code": "1111"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"🔑 Client Login - Status: {response.status_code}")
        print(f"🔑 Client Login - Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Client Login Error: {e}")
        return False

def test_client_register():
    """Тест регистрации клиента"""
    print("🧪 Тестируем регистрацию клиента...")
    
    url = f"{BASE_URL}/api/clients/register"
    data = {
        "first_name": "Тест",
        "last_name": "Клиент",
        "phone_number": "+9961111111111",
        "email": "test@example.com",
        "preferred_payment_method": "cash"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"📝 Client Register - Status: {response.status_code}")
        print(f"📝 Client Register - Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Client Register Error: {e}")
        return False

def test_health():
    """Тест здоровья сервера"""
    print("🧪 Тестируем здоровье сервера...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"💚 Health - Status: {response.status_code}")
        print(f"💚 Health - Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов клиентских API endpoints...")
    print("=" * 50)
    
    # Тестируем здоровье сервера
    health_ok = test_health()
    print()
    
    if health_ok:
        # Тестируем SMS отправку
        sms_ok = test_sms_send()
        print()
        
        # Тестируем авторизацию клиента
        login_ok = test_client_login()
        print()
        
        # Тестируем регистрацию клиента
        register_ok = test_client_register()
        print()
        
        print("=" * 50)
        print("📊 Результаты тестов:")
        print(f"💚 Health: {'✅' if health_ok else '❌'}")
        print(f"📱 SMS Send: {'✅' if sms_ok else '❌'}")
        print(f"🔑 Client Login: {'✅' if login_ok else '❌'}")
        print(f"📝 Client Register: {'✅' if register_ok else '❌'}")
    else:
        print("❌ Сервер недоступен!")
