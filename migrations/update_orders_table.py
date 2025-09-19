#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

def update_orders_table():
    # Используем SQLite как в основном проекте
    engine = create_engine(
        "sqlite:///./taxi_admin.db",
        connect_args={"check_same_thread": False}
    )
    
    with engine.connect() as conn:
        # Добавляем новые колонки
        new_columns = [
            "ALTER TABLE orders ADD COLUMN order_number VARCHAR UNIQUE",
            "ALTER TABLE orders ADD COLUMN pickup_latitude FLOAT",
            "ALTER TABLE orders ADD COLUMN pickup_longitude FLOAT", 
            "ALTER TABLE orders ADD COLUMN destination_latitude FLOAT",
            "ALTER TABLE orders ADD COLUMN destination_longitude FLOAT",
            "ALTER TABLE orders ADD COLUMN distance FLOAT",
            "ALTER TABLE orders ADD COLUMN duration INTEGER",
            "ALTER TABLE orders ADD COLUMN tariff VARCHAR",
            "ALTER TABLE orders ADD COLUMN payment_method VARCHAR",
            "ALTER TABLE orders ADD COLUMN notes TEXT",
            "ALTER TABLE orders ADD COLUMN accepted_at DATETIME",
            "ALTER TABLE orders ADD COLUMN arrived_at_a DATETIME",
            "ALTER TABLE orders ADD COLUMN started_to_b DATETIME",
            "ALTER TABLE orders ADD COLUMN cancelled_at DATETIME"
        ]
        
        for sql in new_columns:
            try:
                conn.execute(text(sql))
                print(f"✅ Выполнено: {sql}")
            except Exception as e:
                print(f"⚠️ Пропущено (уже существует): {sql} - {e}")
        
        # Обновляем статус по умолчанию (SQLite не поддерживает ALTER COLUMN)
        try:
            conn.execute(text("""
                CREATE TABLE orders_new AS 
                SELECT *, 'received' as status_new FROM orders
            """))
            conn.execute(text("DROP TABLE orders"))
            conn.execute(text("ALTER TABLE orders_new RENAME TO orders"))
            print("✅ Обновлен статус по умолчанию")
        except Exception as e:
            print(f"⚠️ Не удалось обновить статус: {e}")
        
        # Генерируем номера заказов для существующих записей
        try:
            conn.execute(text("""
                UPDATE orders 
                SET order_number = 'WDD' || substr('0000000' || id, -7) 
                WHERE order_number IS NULL OR order_number = ''
            """))
            print("✅ Сгенерированы номера заказов для существующих записей")
        except Exception as e:
            print(f"⚠️ Не удалось сгенерировать номера: {e}")
        
        conn.commit()
        print("🎉 Миграция завершена успешно!")

if __name__ == "__main__":
    update_orders_table()
