#!/usr/bin/env python3
"""
Миграция для добавления счетчиков водителей и диспетчеров в таблицу taxiparks
"""

import sqlite3
import os
from datetime import datetime

def migrate():
    """Добавить поля drivers_count и dispatchers_count в таблицу taxiparks"""
    
    db_path = "taxi_admin.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Начинаем миграцию: добавление счетчиков в taxiparks...")
        
        # Проверяем, существуют ли уже эти поля
        cursor.execute("PRAGMA table_info(taxiparks)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'drivers_count' not in columns:
            print("➕ Добавляем поле drivers_count...")
            cursor.execute("ALTER TABLE taxiparks ADD COLUMN drivers_count INTEGER DEFAULT 0")
        else:
            print("✅ Поле drivers_count уже существует")
            
        if 'dispatchers_count' not in columns:
            print("➕ Добавляем поле dispatchers_count...")
            cursor.execute("ALTER TABLE taxiparks ADD COLUMN dispatchers_count INTEGER DEFAULT 0")
        else:
            print("✅ Поле dispatchers_count уже существует")
        
        # Обновляем счетчики для существующих таксопарков
        print("📊 Обновляем счетчики для существующих таксопарков...")
        
        # Считаем водителей для каждого таксопарка
        cursor.execute("""
            UPDATE taxiparks 
            SET drivers_count = (
                SELECT COUNT(*) 
                FROM drivers 
                WHERE drivers.taxipark_id = taxiparks.id
            )
        """)
        
        # Считаем диспетчеров для каждого таксопарка
        cursor.execute("""
            UPDATE taxiparks 
            SET dispatchers_count = (
                SELECT COUNT(*) 
                FROM administrators 
                WHERE administrators.taxipark_id = taxiparks.id
            )
        """)
        
        conn.commit()
        
        # Проверяем результат
        cursor.execute("SELECT id, name, drivers_count, dispatchers_count FROM taxiparks")
        results = cursor.fetchall()
        
        print("📋 Результат обновления счетчиков:")
        for row in results:
            print(f"  🏢 {row[1]} (ID: {row[0]}): водителей={row[2]}, диспетчеров={row[3]}")
        
        print("✅ Миграция успешно завершена!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 МИГРАЦИЯ: Добавление счетчиков в taxiparks")
    print("=" * 60)
    
    success = migrate()
    
    if success:
        print("🎉 Миграция завершена успешно!")
    else:
        print("💥 Миграция завершилась с ошибкой!")
    
    print("=" * 60)
