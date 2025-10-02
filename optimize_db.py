#!/usr/bin/env python3
"""
Скрипт для оптимизации базы данных
Добавляет индексы для ускорения поиска
"""

import sqlite3
import os

def optimize_database():
    """Оптимизирует базу данных для быстрого поиска"""
    
    # Путь к основной БД (SQLAlchemy)
    main_db_path = "taxi_admin.db"
    
    if not os.path.exists(main_db_path):
        print(f"❌ База данных {main_db_path} не найдена")
        return
    
    try:
        conn = sqlite3.connect(main_db_path)
        cursor = conn.cursor()
        
        print("🔧 Оптимизация базы данных...")
        
        # Добавляем индекс для быстрого поиска водителей по номеру телефона
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_drivers_phone_number 
                ON drivers(phone_number)
            ''')
            print("✅ Индекс для drivers.phone_number создан")
        except Exception as e:
            print(f"⚠️ Ошибка создания индекса drivers.phone_number: {e}")
        
        # Добавляем индекс для быстрого поиска по статусу активности
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_drivers_is_active 
                ON drivers(is_active)
            ''')
            print("✅ Индекс для drivers.is_active создан")
        except Exception as e:
            print(f"⚠️ Ошибка создания индекса drivers.is_active: {e}")
        
        # Добавляем индекс для быстрого поиска по таксопарку
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_drivers_taxipark_id 
                ON drivers(taxipark_id)
            ''')
            print("✅ Индекс для drivers.taxipark_id создан")
        except Exception as e:
            print(f"⚠️ Ошибка создания индекса drivers.taxipark_id: {e}")
        
        # Анализируем базу данных для оптимизации запросов
        cursor.execute('ANALYZE')
        print("✅ Анализ базы данных выполнен")
        
        conn.commit()
        conn.close()
        
        print("🎉 Оптимизация базы данных завершена!")
        
    except Exception as e:
        print(f"❌ Ошибка оптимизации базы данных: {e}")

if __name__ == "__main__":
    optimize_database()
