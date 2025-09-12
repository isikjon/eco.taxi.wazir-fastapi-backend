#!/usr/bin/env python3
"""
Скрипт для обновления счетчиков водителей и диспетчеров во всех таксопарках
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models.taxipark import TaxiPark
from app.models.driver import Driver
from app.models.administrator import Administrator

def update_all_taxipark_counts():
    db = SessionLocal()
    
    try:
        taxiparks = db.query(TaxiPark).all()
        print(f"🔍 Найдено таксопарков: {len(taxiparks)}")
        
        for taxipark in taxiparks:
            # Подсчитываем водителей
            drivers_count = db.query(Driver).filter(Driver.taxipark_id == taxipark.id).count()
            
            # Подсчитываем диспетчеров
            dispatchers_count = db.query(Administrator).filter(Administrator.taxipark_id == taxipark.id).count()
            
            # Обновляем счетчики
            taxipark.drivers_count = drivers_count
            taxipark.dispatchers_count = dispatchers_count
            
            print(f"✅ {taxipark.name}: {drivers_count} водителей, {dispatchers_count} диспетчеров")
        
        db.commit()
        print("✅ Все счетчики обновлены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Обновление счетчиков таксопарков...")
    update_all_taxipark_counts()
