#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_login():
    """Тестируем логин клиента"""
    url = "http://127.0.0.1:8080/api/clients/login"
    
    # Тестовые данные
    data = {
        "phone_number": "+9965181515989",
        "sms_code": "1111"
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "EcoTaxiApp/1.0.0"
    }
    
    print(f"🔑 Тестируем логин клиента...")
    print(f"   URL: {url}")
    print(f"   Данные: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        print(f"   Статус: {response.status_code}")
        print(f"   Ответ: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Успех: {result.get('success', False)}")
            print(f"   Новый пользователь: {result.get('data', {}).get('isNewUser', False)}")
        else:
            print(f"   ❌ Ошибка HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка запроса: {e}")

if __name__ == "__main__":
    test_login()
