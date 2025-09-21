#!/usr/bin/env python3
"""
Скрипт для добавления тестовых партнеров (таксопарков) в базу данных
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models.partner import Partner
from datetime import datetime

def add_test_partners():
    """Добавляем тестовых партнеров в базу данных"""
    
    db = SessionLocal()
    
    try:
        # Проверяем, есть ли уже партнеры
        existing_partners = db.query(Partner).count()
        if existing_partners > 0:
            print(f"✅ В базе уже есть {existing_partners} партнеров")
            return
        
        # Создаем тестовых партнеров
        test_partners = [
            {
                "name": "ИП Степанов",
                "commission": 15.0,
                "is_active": True,
                "car_count": 25,
                "description": "Надежный таксопарк с современным автопарком. Работаем с 2015 года.",
                "contact_phone": "+996 555 123 456",
                "contact_email": "stepanov@taxi.kg"
            },
            {
                "name": "ООО Быстрый Такси",
                "commission": 12.0,
                "is_active": True,
                "car_count": 40,
                "description": "Крупнейший таксопарк города. Более 40 автомобилей различных классов.",
                "contact_phone": "+996 555 234 567",
                "contact_email": "info@fasttaxi.kg"
            },
            {
                "name": "ИП Козлов",
                "commission": 18.0,
                "is_active": True,
                "car_count": 15,
                "description": "Семейный таксопарк с индивидуальным подходом к каждому клиенту.",
                "contact_phone": "+996 555 345 678",
                "contact_email": "kozlov@taxi.kg"
            },
            {
                "name": "ТОО Эко Такси",
                "commission": 10.0,
                "is_active": True,
                "car_count": 30,
                "description": "Экологически чистый таксопарк. Используем только гибридные автомобили.",
                "contact_phone": "+996 555 456 789",
                "contact_email": "eco@taxi.kg"
            },
            {
                "name": "ИП Морозов",
                "commission": 20.0,
                "is_active": True,
                "car_count": 8,
                "description": "Премиум таксопарк с автомобилями бизнес-класса.",
                "contact_phone": "+996 555 567 890",
                "contact_email": "morozov@premium.kg"
            }
        ]
        
        for partner_data in test_partners:
            partner = Partner(
                name=partner_data["name"],
                commission=partner_data["commission"],
                is_active=partner_data["is_active"],
                car_count=partner_data["car_count"],
                description=partner_data["description"],
                contact_phone=partner_data["contact_phone"],
                contact_email=partner_data["contact_email"],
                created_at=datetime.now()
            )
            db.add(partner)
        
        db.commit()
        print(f"✅ Добавлено {len(test_partners)} тестовых партнеров:")
        
        for partner_data in test_partners:
            print(f"   🚗 {partner_data['name']} - {partner_data['car_count']} машин, комиссия {partner_data['commission']}%")
        
        print("✅ Тестовые партнеры успешно добавлены в базу данных!")
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении партнеров: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_test_partners()
