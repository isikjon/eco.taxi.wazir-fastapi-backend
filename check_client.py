#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys

def check_client(phone_number):
    """Проверяем клиента в базе данных"""
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect('taxi_admin.db')
        cursor = conn.cursor()
        
        print(f"🔍 Проверяем клиента с номером: {phone_number}")
        
        # Ищем клиента
        cursor.execute("SELECT * FROM clients WHERE phone_number = ?", (phone_number,))
        client = cursor.fetchone()
        
        if client:
            print("✅ Клиент найден в базе данных:")
            print(f"   ID: {client[0]}")
            print(f"   Имя: {client[1]}")
            print(f"   Фамилия: {client[2]}")
            print(f"   Телефон: {client[3]}")
            print(f"   Email: {client[4]}")
            print(f"   Рейтинг: {client[5]}")
            print(f"   Всего поездок: {client[6]}")
            print(f"   Потрачено: {client[7]}")
            print(f"   Способ оплаты: {client[8]}")
            print(f"   Активен: {client[9]}")
            print(f"   Создан: {client[10]}")
            print(f"   Обновлен: {client[11]}")
        else:
            print("❌ Клиент НЕ найден в базе данных")
            print("   Это означает, что это новый пользователь")
            
            # Показываем всех клиентов
            cursor.execute("SELECT phone_number, first_name, last_name FROM clients")
            all_clients = cursor.fetchall()
            print(f"\n📋 Всего клиентов в базе: {len(all_clients)}")
            for client in all_clients:
                print(f"   - {client[0]} ({client[1]} {client[2]})")
        
        conn.close()
        return client is not None
        
    except Exception as e:
        print(f"❌ Ошибка при проверке клиента: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python check_client.py <номер_телефона>")
        print("Пример: python check_client.py +9965181515181")
        sys.exit(1)
    
    phone_number = sys.argv[1]
    check_client(phone_number)
