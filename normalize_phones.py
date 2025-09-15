#!/usr/bin/env python3
"""
Скрипт для нормализации всех номеров телефонов в базе данных
к единому формату: +996XXXXXXXXX (слитно с префиксом +996)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import get_db
from app.models.driver import Driver
from sqlalchemy.orm import Session

def normalize_phone_number(phone: str) -> str:
    """Нормализует номер телефона к формату +996XXXXXXXXX"""
    if not phone:
        return phone
    
    # Извлекаем только цифры
    digits_only = ''.join(filter(str.isdigit, phone))
    
    # Определяем основные 9 цифр номера
    if len(digits_only) >= 9:
        if digits_only.startswith('996') and len(digits_only) >= 12:
            # Номер с кодом страны 996
            main_digits = digits_only[3:12]  # Берем 9 цифр после 996
        else:
            # Берем последние 9 цифр
            main_digits = digits_only[-9:]
    else:
        return phone  # Не можем нормализовать
    
    # Возвращаем в формате +996XXXXXXXXX
    return f"+996{main_digits}"

def main():
    print("🔄 Начинаем нормализацию номеров телефонов в базе данных...")
    
    # Получаем сессию базы данных
    db = next(get_db())
    
    try:
        # Получаем всех водителей
        drivers = db.query(Driver).all()
        print(f"📋 Найдено водителей в БД: {len(drivers)}")
        
        # Группируем изменения и проверяем дубликаты
        phone_changes = {}
        duplicate_count = {}
        
        for driver in drivers:
            old_phone = driver.phone_number
            new_phone = normalize_phone_number(old_phone)
            
            if old_phone != new_phone:
                print(f"📞 ID: {driver.id}, Имя: {driver.first_name} {driver.last_name}")
                print(f"   Старый: '{old_phone}' -> Новый: '{new_phone}'")
                
                # Проверяем дубликаты
                if new_phone in duplicate_count:
                    duplicate_count[new_phone] += 1
                    # Добавляем суффикс для дубликатов
                    unique_phone = f"{new_phone[:-1]}{duplicate_count[new_phone]}"
                    print(f"   ⚠️  Дубликат! Изменяем на: '{unique_phone}'")
                    phone_changes[driver.id] = unique_phone
                else:
                    duplicate_count[new_phone] = 1
                    phone_changes[driver.id] = new_phone
            else:
                print(f"✅ ID: {driver.id}, Номер уже нормализован: '{old_phone}'")
        
        # Применяем изменения
        updated_count = 0
        for driver_id, new_phone in phone_changes.items():
            driver = db.query(Driver).filter(Driver.id == driver_id).first()
            if driver:
                driver.phone_number = new_phone
                updated_count += 1
        
        if updated_count > 0:
            # Сохраняем изменения
            db.commit()
            print(f"\n✅ Обновлено номеров: {updated_count}")
        else:
            print("\n✅ Все номера уже в правильном формате")
        
        # Показываем финальное состояние
        print("\n📋 Финальное состояние БД:")
        drivers = db.query(Driver).all()
        for driver in drivers:
            print(f"   ID: {driver.id}, Phone: '{driver.phone_number}', Name: {driver.first_name} {driver.last_name}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
