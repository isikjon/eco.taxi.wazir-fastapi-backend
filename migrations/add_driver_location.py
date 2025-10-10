"""
Миграция для добавления полей current_latitude и current_longitude в таблицу drivers
"""
import sqlite3

def run_migration():
    conn = sqlite3.connect('taxi_admin.db')
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли уже поле current_latitude
        cursor.execute("PRAGMA table_info(drivers)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'current_latitude' not in columns:
            print("🔄 Добавляем поле current_latitude...")
            cursor.execute("ALTER TABLE drivers ADD COLUMN current_latitude REAL")
            print("✅ Поле current_latitude добавлено")
        else:
            print("ℹ️ Поле current_latitude уже существует")
        
        if 'current_longitude' not in columns:
            print("🔄 Добавляем поле current_longitude...")
            cursor.execute("ALTER TABLE drivers ADD COLUMN current_longitude REAL")
            print("✅ Поле current_longitude добавлено")
        else:
            print("ℹ️ Поле current_longitude уже существует")
        
        conn.commit()
        print("✅ Миграция завершена успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()

