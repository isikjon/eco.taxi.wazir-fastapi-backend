#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys
from datetime import datetime

def check_sms_codes(phone_number):
    """Проверяем SMS коды в базе данных"""
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect('taxi_admin.db')
        cursor = conn.cursor()
        
        print(f"🔍 Проверяем SMS коды для номера: {phone_number}")
        
        # Проверяем таблицу sms_codes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sms_codes'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ Таблица 'sms_codes' не существует!")
            return False
        
        # Ищем SMS коды для этого номера
        cursor.execute("SELECT * FROM sms_codes WHERE phone_number = ? ORDER BY created_at DESC", (phone_number,))
        sms_codes = cursor.fetchall()
        
        if sms_codes:
            print(f"✅ Найдено {len(sms_codes)} SMS кодов:")
            for sms in sms_codes:
                print(f"   - Код: {sms[1]}, Использован: {sms[3]}, Создан: {sms[4]}, Истекает: {sms[5]}")
        else:
            print("❌ SMS коды не найдены для этого номера")
            
            # Показываем все SMS коды
            cursor.execute("SELECT phone_number, code, used, created_at, expires_at FROM sms_codes ORDER BY created_at DESC LIMIT 10")
            all_sms = cursor.fetchall()
            print(f"\n📋 Последние 10 SMS кодов в базе:")
            for sms in all_sms:
                print(f"   - {sms[0]}: {sms[1]} (использован: {sms[2]}, создан: {sms[3]}, истекает: {sms[4]})")
        
        conn.close()
        return len(sms_codes) > 0
        
    except Exception as e:
        print(f"❌ Ошибка при проверке SMS кодов: {e}")
        return False

def add_test_sms_code(phone_number, code="1111"):
    """Добавляем тестовый SMS код"""
    try:
        conn = sqlite3.connect('taxi_admin.db')
        cursor = conn.cursor()
        
        # Создаем таблицу если не существует
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sms_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number VARCHAR(20) NOT NULL,
                code VARCHAR(10) NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP DEFAULT (datetime('now', '+5 minutes'))
            )
        ''')
        
        # Добавляем тестовый код
        cursor.execute('''
            INSERT INTO sms_codes (phone_number, code, used, expires_at)
            VALUES (?, ?, FALSE, datetime('now', '+5 minutes'))
        ''', (phone_number, code))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Добавлен тестовый SMS код {code} для номера {phone_number}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении SMS кода: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python check_sms.py <номер_телефона> [add]")
        print("Пример: python check_sms.py +9965181515189")
        print("Пример: python check_sms.py +9965181515189 add")
        sys.exit(1)
    
    phone_number = sys.argv[1]
    should_add = len(sys.argv) > 2 and sys.argv[2] == "add"
    
    if should_add:
        add_test_sms_code(phone_number)
    
    check_sms_codes(phone_number)
