#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.driver import Driver

def update_test_driver():
    db = SessionLocal()
    try:
        # Находим тестового водителя
        test_driver = db.query(Driver).filter(Driver.phone_number == "+996111111111").first()
        if not test_driver:
            print("❌ Тестовый водитель не найден")
            return None

        print("🔍 Найден тестовый водитель:")
        print(f"   ID: {test_driver.id}")
        print(f"   Имя: {test_driver.first_name} {test_driver.last_name}")
        print(f"   Телефон: {test_driver.phone_number}")
        print(f"   Машина: {test_driver.car_model} {test_driver.car_number}")
        print()

        # Обновляем данные
        test_driver.car_model = "BYD Han"
        test_driver.car_number = "01 77 7 77777"
        test_driver.car_color = "Белый"
        test_driver.car_year = "2023"
        test_driver.car_vin = "BYD123456789"
        test_driver.car_body_number = "BYD123456"
        test_driver.car_sts = "BYD123456"
        test_driver.tariff = "Комфорт"
        test_driver.balance = 1000.0
        test_driver.is_active = True
        test_driver.photo_verification_status = "approved"

        db.commit()
        db.refresh(test_driver)

        print("✅ Данные тестового водителя обновлены:")
        print(f"   ID: {test_driver.id}")
        print(f"   Имя: {test_driver.first_name} {test_driver.last_name}")
        print(f"   Телефон: {test_driver.phone_number}")
        print(f"   Машина: {test_driver.car_model} {test_driver.car_number}")
        print(f"   Цвет: {test_driver.car_color}")
        print(f"   Год: {test_driver.car_year}")
        print(f"   VIN: {test_driver.car_vin}")
        print(f"   Номер кузова: {test_driver.car_body_number}")
        print(f"   СТС: {test_driver.car_sts}")
        print(f"   Тариф: {test_driver.tariff}")
        print(f"   Баланс: {test_driver.balance} сом")
        print(f"   Статус: {'Активен' if test_driver.is_active else 'Заблокирован'}")
        print(f"   Фотоверификация: {test_driver.photo_verification_status}")
        print()
        print("🔑 Данные для входа:")
        print(f"   Номер телефона: +996 111 111 111")
        print(f"   SMS код: 1111")

        return test_driver

    except Exception as e:
        print(f"❌ Ошибка при обновлении тестового водителя: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("🚗 Обновление тестового водителя...")
    print("=" * 50)
    update_test_driver()
