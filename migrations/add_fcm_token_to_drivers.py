"""
Миграция для добавления поля fcm_token в таблицу drivers
"""

import sqlite3
import os
from pathlib import Path

def run_migration():
    db_path = Path("taxi_admin.db")
    
    if not db_path.exists():
        print("❌ База данных не найдена")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Проверяем, существует ли уже поле fcm_token
        cursor.execute("PRAGMA table_info(drivers)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'fcm_token' in columns:
            print("✅ Поле fcm_token уже существует в таблице drivers")
            return
        
        # Добавляем поле fcm_token
        cursor.execute("ALTER TABLE drivers ADD COLUMN fcm_token TEXT")
        
        conn.commit()
        print("✅ Поле fcm_token добавлено в таблицу drivers")
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
