#!/usr/bin/env python3
"""
Скрипт для добавления тестового водителя
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models.driver import Driver
from app.models.taxipark import TaxiPark

def add_test_driver():
    db = SessionLocal()
    
    try:
        # Проверяем, есть ли таксопарки
        taxiparks = db.query(TaxiPark).all()
        if not taxiparks:
            print("❌ Нет таксопарков в базе данных!")
            return
        
        # Берем первый таксопарк
        taxipark = taxiparks[0]
        print(f"✅ Используем таксопарк: {taxipark.name}")
        
        # Проверяем, есть ли уже водители
        existing_drivers = db.query(Driver).all()
        if existing_drivers:
            print(f"✅ В базе уже есть {len(existing_drivers)} водителей")
            for driver in existing_drivers:
                print(f"  - {driver.first_name} {driver.last_name} ({driver.phone_number})")
            return
        
        # Создаем тестового водителя
        test_driver = Driver(
            first_name="Иван",
            last_name="Петров",
            phone_number="+996555123456",
            car_model="Toyota Camry",
            car_number="01KG123ABC",
            balance=1500.0,
            tariff="Комфорт",
            taxipark_id=taxipark.id,
            is_active=True
        )
        
        db.add(test_driver)
        db.commit()
        db.refresh(test_driver)
        
        print(f"✅ Тестовый водитель создан: {test_driver.first_name} {test_driver.last_name}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Добавление тестового водителя...")
    add_test_driver()
