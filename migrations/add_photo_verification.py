"""
Миграция для добавления таблицы photo_verifications и поля photo_verification_status в drivers
"""

import sqlite3
import os
from datetime import datetime

def run_migration():
    """Выполнить миграцию базы данных"""
    db_path = "taxi_admin.db"
    
    if not os.path.exists(db_path):
        print("❌ Файл базы данных не найден!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Начинаем миграцию...")
        
        # 1. Добавляем поле photo_verification_status в таблицу drivers
        try:
            cursor.execute("""
                ALTER TABLE drivers 
                ADD COLUMN photo_verification_status VARCHAR DEFAULT 'not_started'
            """)
            print("✅ Добавлено поле photo_verification_status в таблицу drivers")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("ℹ️ Поле photo_verification_status уже существует в таблице drivers")
            else:
                raise e
        
        # 2. Создаем таблицу photo_verifications
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS photo_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_id INTEGER NOT NULL,
                taxipark_id INTEGER NOT NULL,
                status VARCHAR DEFAULT 'pending' NOT NULL,
                photos JSON,
                rejection_reason TEXT,
                processed_by VARCHAR,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                processed_at DATETIME,
                FOREIGN KEY (driver_id) REFERENCES drivers (id),
                FOREIGN KEY (taxipark_id) REFERENCES taxiparks (id)
            )
        """)
        print("✅ Создана таблица photo_verifications")
        
        # 3. Обновляем статус существующих водителей
        cursor.execute("""
            UPDATE drivers 
            SET photo_verification_status = CASE 
                WHEN is_active = 1 THEN 'approved'
                WHEN is_active = 0 THEN 'rejected'
                ELSE 'not_started'
            END
            WHERE photo_verification_status = 'not_started'
        """)
        updated_drivers = cursor.rowcount
        print(f"✅ Обновлен статус фотоверификации для {updated_drivers} водителей")
        
        # Сохраняем изменения
        conn.commit()
        print("✅ Миграция успешно завершена!")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("🎉 База данных успешно обновлена!")
    else:
        print("💥 Миграция не удалась!")
