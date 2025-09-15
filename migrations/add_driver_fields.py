"""
Миграция для добавления новых полей в таблицу drivers
"""
import sqlite3
import os

def migrate_database():
    """Добавляет новые поля в таблицу drivers"""
    
    # Путь к базе данных
    db_path = "taxi_admin.db"
    
    if not os.path.exists(db_path):
        print("База данных не найдена. Создайте базу данных сначала.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, существуют ли уже новые поля
        cursor.execute("PRAGMA table_info(drivers)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Добавляем новые поля, если их еще нет
        new_fields = [
            ("car_color", "TEXT"),
            ("car_year", "TEXT"),
            ("car_vin", "TEXT"),
            ("car_body_number", "TEXT"), 
            ("car_sts", "TEXT"),
            ("call_sign", "TEXT")
        ]
        
        for field_name, field_type in new_fields:
            if field_name not in columns:
                cursor.execute(f"ALTER TABLE drivers ADD COLUMN {field_name} {field_type}")
                print(f"✅ Добавлено поле {field_name}")
            else:
                print(f"⚠️ Поле {field_name} уже существует")
        
        conn.commit()
        print("✅ Миграция завершена успешно")
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
