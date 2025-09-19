#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

def fix_order_number():
    # Используем SQLite как в основном проекте
    engine = create_engine(
        "sqlite:///./taxi_admin.db",
        connect_args={"check_same_thread": False}
    )
    
    with engine.connect() as conn:
        try:
            # Создаем новую таблицу с правильной структурой
            conn.execute(text("""
                CREATE TABLE orders_new (
                    id INTEGER PRIMARY KEY,
                    order_number VARCHAR UNIQUE NOT NULL,
                    client_name VARCHAR,
                    client_phone VARCHAR,
                    pickup_address VARCHAR NOT NULL,
                    pickup_latitude FLOAT,
                    pickup_longitude FLOAT,
                    destination_address VARCHAR NOT NULL,
                    destination_latitude FLOAT,
                    destination_longitude FLOAT,
                    price FLOAT DEFAULT 0.0,
                    distance FLOAT,
                    duration INTEGER,
                    status VARCHAR DEFAULT 'received',
                    driver_id INTEGER,
                    taxipark_id INTEGER NOT NULL,
                    tariff VARCHAR,
                    payment_method VARCHAR,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    accepted_at DATETIME,
                    arrived_at_a DATETIME,
                    started_to_b DATETIME,
                    completed_at DATETIME,
                    cancelled_at DATETIME,
                    FOREIGN KEY (driver_id) REFERENCES drivers (id),
                    FOREIGN KEY (taxipark_id) REFERENCES taxiparks (id)
                )
            """))
            print("✅ Создана новая таблица orders_new")
            
            # Копируем данные из старой таблицы
            conn.execute(text("""
                INSERT INTO orders_new (
                    id, client_name, client_phone, pickup_address, pickup_latitude, pickup_longitude,
                    destination_address, destination_latitude, destination_longitude, price, distance, duration,
                    status, driver_id, taxipark_id, tariff, payment_method, notes,
                    created_at, accepted_at, arrived_at_a, started_to_b, completed_at, cancelled_at
                )
                SELECT 
                    id, client_name, client_phone, pickup_address, pickup_latitude, pickup_longitude,
                    destination_address, destination_latitude, destination_longitude, price, distance, duration,
                    COALESCE(status, 'received'), driver_id, taxipark_id, tariff, payment_method, notes,
                    created_at, accepted_at, arrived_at_a, started_to_b, completed_at, cancelled_at
                FROM orders
            """))
            print("✅ Скопированы данные в новую таблицу")
            
            # Генерируем номера заказов
            conn.execute(text("""
                UPDATE orders_new 
                SET order_number = 'WDD' || substr('0000000' || id, -7) 
                WHERE order_number IS NULL OR order_number = ''
            """))
            print("✅ Сгенерированы номера заказов")
            
            # Удаляем старую таблицу и переименовываем новую
            conn.execute(text("DROP TABLE orders"))
            conn.execute(text("ALTER TABLE orders_new RENAME TO orders"))
            print("✅ Заменена таблица orders")
            
            conn.commit()
            print("🎉 Исправление завершено успешно!")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            conn.rollback()

if __name__ == "__main__":
    fix_order_number()
