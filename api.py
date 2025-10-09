from fastapi import HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import json
import hashlib
import uuid
from datetime import datetime
import os

from app.database.session import get_db, SessionLocal

# Путь к базе данных
DB_PATH = "taxi_admin.db"

# API для обновления статуса заказа водителем
async def update_order_status_by_driver(order_id: int, request: Request):
    """Обновить статус заказа водителем"""
    try:
        data = await request.json()
        status = data.get('status')
        driver_id = data.get('driver_id')
        timestamp = data.get('timestamp')
        
        if not status or not driver_id:
            raise HTTPException(status_code=400, detail="Status and driver_id are required")
        
        valid_statuses = ['accepted', 'navigating_to_a', 'arrived_at_a', 'navigating_to_b', 'completed', 'cancelled']
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        # Получаем сессию БД
        db = SessionLocal()
        
        try:
            from app.models.order import Order
            from app.models.driver import Driver
            from datetime import datetime
            
            # Проверяем водителя
            driver = db.query(Driver).filter(Driver.id == driver_id).first()
            if not driver:
                raise HTTPException(status_code=404, detail="Driver not found")
            
            # Находим заказ
            order = db.query(Order).filter(
                Order.id == order_id,
                Order.driver_id == driver_id
            ).first()
            
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            # Обновляем статус
            old_status = order.status
            order.status = status
            
            # Обновляем временные метки
            now = datetime.now()
            if status == "accepted":
                order.accepted_at = now
            elif status == "arrived_at_a":
                order.arrived_at_a = now
            elif status == "navigating_to_b":
                order.started_to_b = now
            elif status == "completed":
                order.completed_at = now
            elif status == "cancelled":
                order.cancelled_at = now
            
            db.commit()
            
            # Отправляем обновление через WebSocket
            from app.websocket.manager import websocket_manager
            await websocket_manager.send_to_taxipark({
                "type": "order_status_changed",
                "order_id": order_id,
                "order_number": order.order_number,
                "old_status": old_status,
                "new_status": status,
                "driver_id": str(driver_id),
                "timestamp": timestamp or now.isoformat()
            }, order.taxipark_id, exclude_user=str(driver_id))
            
            return {
                "success": True,
                "message": "Order status updated successfully",
                "order_id": order_id,
                "old_status": old_status,
                "new_status": status
            }
            
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# События запуска и остановки приложения
async def startup_event():
    """Инициализация при запуске приложения"""
    try:
        from app.database.init_db import init_database
        init_database()
        print("✅ SQLAlchemy database initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing SQLAlchemy database: {e}")
    
    # Создание SQLite базы данных для API
    create_database()

# Pydantic модели
class DriverRegistration(BaseModel):
    user: dict
    car: dict
    park: dict
    timestamp: str

class DriverLogin(BaseModel):
    phoneNumber: str
    smsCode: str

class SmsRequest(BaseModel):
    phoneNumber: str

# Функция для подключения к БД SQLite (только для SMS)
def get_db_connection():
    if not os.path.exists(DB_PATH):
        # Создаем базу данных если она не существует
        create_database()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Возвращать результаты как словари
    return conn

# Создание структуры БД (только для SMS кодов)
def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Удаляем старые таблицы если они есть
    cursor.execute('DROP TABLE IF EXISTS sms_codes')
    
    # Создаем только таблицу SMS кодов для мобильного приложения
    cursor.execute('''
        CREATE TABLE sms_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT NOT NULL,
            code TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("SMS database created successfully!")

# Функция нормализации номера телефона
def normalize_phone_number(phone_number):
    """Нормализует номер телефона к единому формату +996XXXXXXXXXX для поиска в БД"""
    if not phone_number:
        return None
    
    # Извлекаем только цифры из номера
    digits_only = ''.join(filter(str.isdigit, phone_number))
    
    # Определяем основные цифры номера
    if len(digits_only) >= 10:
        if digits_only.startswith('996'):
            # Номер с кодом страны 996 - берем все цифры после 996
            main_digits = digits_only[3:]  # Берем все цифры после 996
        else:
            # Берем последние 10 цифр, если их достаточно
            main_digits = digits_only[-10:] if len(digits_only) >= 10 else digits_only[-9:]
    else:
        return None  # Не можем нормализовать
    
    # Возвращаем в едином формате БД: +996XXXXXXXXXX
    return f"+996{main_digits}"

# API endpoints

async def root():
    return {"message": "Taxi Driver Registration API", "version": "1.0.0"}

async def get_parks(db: SessionLocal = Depends(get_db)):
    """Получить список всех таксопарков"""
    try:
        from sqlalchemy.orm import Session
        from app.models.taxipark import TaxiPark
        
        taxiparks = db.query(TaxiPark).filter(TaxiPark.is_active == True).order_by(TaxiPark.name).all()
        
        parks = []
        for taxipark in taxiparks:
            parks.append({
                'id': taxipark.id,
                'name': taxipark.name,
                'city': taxipark.city,
                'phone': taxipark.phone,
                'email': taxipark.email,
                'address': taxipark.address,
                'working_hours': taxipark.working_hours,
                'commission_percent': taxipark.commission_percent,
                'description': taxipark.description
            })
        
        return {"parks": parks, "count": len(parks)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

async def send_sms_code(request: SmsRequest):
    """Отправить SMS код через Devino 2FA API"""
    try:
        import requests
        from datetime import datetime
        
        # Нормализуем номер телефона
        normalized_phone = normalize_phone_number(request.phoneNumber)
        if not normalized_phone:
            raise HTTPException(status_code=400, detail="Неверный формат номера телефона")
        
        # Проверяем тестовый номер
        if normalized_phone == "+996111111111":
            return {
                "success": True,
                "message": "SMS код отправлен (тестовый режим)",
                "messageId": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "provider": "test_mode",
                "test_code": "1111"
            }
        
        # Нормализуем номер для Devino 2FA API (убираем +)
        phone_for_2fa = normalized_phone.replace('+', '')
        
        # Devino 2FA API настройки
        devino_2fa_url = "https://phoneverification.devinotele.com/GenerateCode"
        devino_api_key = "8YF4D4R8k094r8uR3nwiEnsRuwIXRW67"
        
        # Отправляем запрос на генерацию кода через Devino 2FA API
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-ApiKey": devino_api_key
        }
        
        payload = {
            "DestinationNumber": phone_for_2fa
        }
        
        response = requests.post(
            devino_2fa_url,
            headers=headers,
            json=payload,
            timeout=10  # Уменьшили таймаут с 30 до 10 секунд
        )
        
        if response.status_code == 200:
            response_data = response.json()
            
            if response_data.get('Code') == 0:
                # SMS код успешно отправлен через Devino 2FA
                return {
                    "success": True,
                    "message": "SMS код отправлен",
                    "messageId": f"devino_2fa_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "provider": "devino_2fa",
                    "description": response_data.get('Description')
                }
            else:
                # Ошибка от Devino API
                error_desc = response_data.get('Description', 'Неизвестная ошибка')
                raise HTTPException(status_code=400, detail=f"Devino API error: {error_desc}")
        else:
            # HTTP ошибка
            raise HTTPException(status_code=500, detail=f"HTTP error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMS sending error: {str(e)}")

async def check_sms_code_with_devino(phone_number: str, code: str):
    """Проверить SMS код через Devino 2FA API"""
    try:
        import requests
        
        # Нормализуем номер телефона
        normalized_phone = normalize_phone_number(phone_number)
        if not normalized_phone:
            return {"valid": False, "error": "Неверный формат номера телефона"}
        
        # Проверяем тестовый номер
        if normalized_phone == "+996111111111":
            if code == "1111":
                return {
                    "valid": True,
                    "message": "Тестовый код принят"
                }
            else:
                return {
                    "valid": False,
                    "error": "Неверный тестовый код"
                }
        
        # Нормализуем номер для Devino 2FA API (убираем +)
        phone_for_2fa = normalized_phone.replace('+', '')
        
        # Devino 2FA API настройки
        devino_check_url = "https://phoneverification.devinotele.com/CheckCode"
        devino_api_key = "8YF4D4R8k094r8uR3nwiEnsRuwIXRW67"
        
        # Отправляем запрос на проверку кода через Devino 2FA API
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-ApiKey": devino_api_key
        }
        
        payload = {
            "DestinationNumber": phone_for_2fa,
            "Code": code
        }
        
        response = requests.post(
            devino_check_url,
            headers=headers,
            json=payload,
            timeout=10  # Уменьшили таймаут с 30 до 10 секунд
        )
        
        if response.status_code == 200:
            response_data = response.json()
            
            if response_data.get('Code') == 0:
                # Код валидный
                return {
                    "valid": True,
                    "message": response_data.get('Description')
                }
            else:
                # Код невалидный
                error_desc = response_data.get('Description', 'Неизвестная ошибка')
                return {
                    "valid": False,
                    "error": error_desc
                }
        else:
            # HTTP ошибка
            return {
                "valid": False,
                "error": f"HTTP error: {response.status_code}"
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "valid": False,
            "error": f"Connection error: {str(e)}"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Check error: {str(e)}"
        }


async def login_driver(request: DriverLogin, db: SessionLocal = Depends(get_db)):
    """Авторизация водителя по номеру телефона и SMS коду"""
    try:
        from app.models.driver import Driver
        from datetime import datetime
        
        print("=" * 80)
        print(f"🔐 [LOGIN] ===== НАЧАЛО АВТОРИЗАЦИИ ВОДИТЕЛЯ =====")
        print(f"🕐 [LOGIN] Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📞 [LOGIN] Номер телефона: {request.phoneNumber}")
        print(f"🔢 [LOGIN] SMS код: {request.smsCode}")
        
        normalized_phone = normalize_phone_number(request.phoneNumber)
        print(f"📱 [LOGIN] Нормализованный номер: {normalized_phone}")
        
        print(f"🔍 [LOGIN] Проверка SMS кода через Devino 2FA...")
        check_result = await check_sms_code_with_devino(request.phoneNumber, request.smsCode)
        
        if not check_result['valid']:
            print(f"❌ [LOGIN] SMS код невалидный: {check_result.get('error', 'Неизвестная ошибка')}")
            raise HTTPException(status_code=400, detail="Неверный или истекший SMS код")
        
        print(f"✅ [LOGIN] SMS код валидный")
        print(f"🔍 [LOGIN] Поиск водителя в БД...")
        
        driver = db.query(Driver).filter(Driver.phone_number == normalized_phone).first()
        
        if driver:
            print(f"✅ [LOGIN] Водитель найден: ID={driver.id}, ФИО={driver.first_name} {driver.last_name}")
            
            if not driver.is_active:
                print(f"❌ [LOGIN] Водитель заблокирован: ID={driver.id}")
                print(f"=" * 80)
                return {
                    "success": False,
                    "error": "blocked",
                    "message": "Ваш аккаунт заблокирован суперадмином. Для связи: +996 559 868 878"
                }
            
            try:
                taxipark_name = driver.taxipark.name if driver.taxipark else "Не указан"
                print(f"🏢 [LOGIN] Таксопарк: {taxipark_name}")
            except Exception:
                taxipark_name = "Не указан"
                print(f"⚠️ [LOGIN] Таксопарк не найден")
            
            driver_data = {
                "id": driver.id,
                "phoneNumber": driver.phone_number,
                "fullName": f"{driver.first_name} {driver.last_name}",
                "carModel": driver.car_model or "Не указана",
                "carNumber": driver.car_number or "Не указан",
                "carBrand": driver.car_model.split(' ')[0] if driver.car_model else "",
                "carColor": driver.car_color or "",
                "carYear": driver.car_year or "",
                "carVin": driver.car_vin or "",
                "carBodyNumber": driver.car_body_number or "",
                "carSts": driver.car_sts or "",
                "taxiparkId": driver.taxipark_id,
                "taxiparkName": taxipark_name,
                "balance": float(driver.balance or 0),
                "status": "active" if driver.is_active else "inactive",
                "blocked": not driver.is_active,
                "blockMessage": "Ваш аккаунт заблокирован суперадмином. Для связи: +996 559 868 878" if not driver.is_active else None
            }
            
            print(f"✅ [LOGIN] Авторизация успешна для существующего водителя")
            print(f"🚗 [LOGIN] Машина: {driver.car_model} {driver.car_number}")
            print(f"💰 [LOGIN] Баланс: {driver.balance}")
            print(f"🔐 [LOGIN] ===== АВТОРИЗАЦИЯ ЗАВЕРШЕНА =====")
            print(f"=" * 80)
            
            return {
                "success": True,
                "isNewUser": False,
                "driver": driver_data
            }
        else:
            print(f"⚠️ [LOGIN] Водитель не найден в БД - новый пользователь")
            print(f"🔐 [LOGIN] ===== ТРЕБУЕТСЯ РЕГИСТРАЦИЯ =====")
            print(f"=" * 80)
            
            return {
                "success": True,
                "isNewUser": True,
                "message": "Новый пользователь, требуется регистрация"
            }
        
    except HTTPException:
        print(f"=" * 80)
        raise
    except Exception as e:
        print(f"❌ [LOGIN] КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        print(f"=" * 80)
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

async def register_driver(registration: DriverRegistration, db: SessionLocal = Depends(get_db)):
    try:
        from app.models.driver import Driver
        from app.models.taxipark import TaxiPark
        from datetime import datetime
        
        print("=" * 80)
        print(f"📝 [REGISTER] ===== НАЧАЛО РЕГИСТРАЦИИ ВОДИТЕЛЯ =====")
        print(f"🕐 [REGISTER] Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        user_data = registration.user
        car_data = registration.car
        park_data = registration.park
        
        print(f"📞 [REGISTER] Номер телефона: {user_data.get('phoneNumber', '')}")
        print(f"👤 [REGISTER] Полное имя: {user_data.get('fullName', '')}")
        print(f"🚗 [REGISTER] Машина: {car_data.get('brand', '')} {car_data.get('model', '')}")
        print(f"🏢 [REGISTER] Таксопарк ID: {park_data.get('id')}")
        print(f"🏢 [REGISTER] Название таксопарка: {park_data.get('name', '')}")
        
        # Нормализуем номер телефона
        normalized_phone = normalize_phone_number(user_data.get('phoneNumber', ''))
        print(f"📱 [REGISTER] Нормализованный номер: {normalized_phone}")
        
        # Проверяем, не существует ли уже водитель с таким номером
        print(f"🔍 [REGISTER] Проверка существования водителя...")
        existing_driver = db.query(Driver).filter(Driver.phone_number == normalized_phone).first()
        if existing_driver:
            print(f"❌ [REGISTER] Водитель с номером {normalized_phone} уже зарегистрирован!")
            print(f"❌ [REGISTER] ID существующего водителя: {existing_driver.id}")
            print(f"❌ [REGISTER] ===== РЕГИСТРАЦИЯ НЕУСПЕШНА =====")
            print("=" * 80)
            raise HTTPException(status_code=400, detail="Водитель с таким номером уже зарегистрирован")
        
        print(f"✅ [REGISTER] Водитель с таким номером не найден, продолжаем регистрацию")
        
        # Проверяем, существует ли таксопарк
        print(f"🔍 [REGISTER] Проверка существования таксопарка...")
        taxipark = db.query(TaxiPark).filter(TaxiPark.id == park_data.get('id')).first()
        if not taxipark:
            print(f"❌ [REGISTER] Таксопарк с ID {park_data.get('id')} не найден!")
            print(f"❌ [REGISTER] ===== РЕГИСТРАЦИЯ НЕУСПЕШНА =====")
            print("=" * 80)
            raise HTTPException(status_code=400, detail="Указанный таксопарк не найден")
        
        print(f"✅ [REGISTER] Таксопарк найден: {taxipark.name}")
        print(f"👥 [REGISTER] Текущее количество водителей в таксопарке: {taxipark.drivers_count or 0}")
        
        # Парсим полное имя
        full_name = user_data.get('fullName', '')
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0] if len(name_parts) > 0 else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        print(f"👤 [REGISTER] Имя: {first_name}")
        print(f"👤 [REGISTER] Фамилия: {last_name}")
        print(f"📞 [REGISTER] Позывной: {user_data.get('callSign', '')}")
        print(f"💰 [REGISTER] Тариф: {user_data.get('tariff', 'Эконом')}")
        
        # Регистрируем нового водителя
        print(f"🆕 [REGISTER] Создание записи водителя в БД...")
        new_driver = Driver(
            phone_number=normalized_phone,
            first_name=first_name,
            last_name=last_name,
            car_model=f"{car_data.get('brand', '')} {car_data.get('model', '')}".strip(),
            car_number=car_data.get('licensePlate', ''),
            car_color=car_data.get('color', ''),
            car_year=car_data.get('year', ''),
            car_vin=car_data.get('vin', ''),
            car_body_number=car_data.get('bodyNumber', ''),
            car_sts=car_data.get('sts', ''),
            call_sign=user_data.get('callSign', ''),
            tariff=user_data.get('tariff', 'Эконом'),
            taxipark_id=park_data.get('id'),
            is_active=True
        )
        
        print(f"💾 [REGISTER] Сохранение водителя в БД...")
        db.add(new_driver)
        db.commit()
        db.refresh(new_driver)
        
        print(f"✅ [REGISTER] Водитель сохранен с ID: {new_driver.id}")
        
        # Обновляем счетчик водителей в таксопарке
        print(f"📊 [REGISTER] Обновление счетчика водителей в таксопарке...")
        from app.services.taxipark_service import TaxiParkService
        TaxiParkService.update_drivers_count(db, new_driver.taxipark_id)
        
        print(f"🎉 [REGISTER] ===== РЕГИСТРАЦИЯ УСПЕШНА =====")
        print(f"🆔 [REGISTER] ID водителя: {new_driver.id}")
        print(f"👤 [REGISTER] Имя: {new_driver.first_name} {new_driver.last_name}")
        print(f"📱 [REGISTER] Номер: {new_driver.phone_number}")
        print(f"🚗 [REGISTER] Машина: {new_driver.car_model}")
        print(f"🏢 [REGISTER] Таксопарк: {taxipark.name}")
        print(f"⏰ [REGISTER] Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        return {
            "success": True,
            "message": "Водитель успешно зарегистрирован",
            "driver_id": new_driver.id,
            "status": "registered"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [REGISTER] Критическая ошибка регистрации: {str(e)}")
        print(f"❌ [REGISTER] ===== РЕГИСТРАЦИЯ НЕУСПЕШНА =====")
        print("=" * 80)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")

async def check_driver_status(phoneNumber: str, db: SessionLocal = Depends(get_db)):
    try:
        from app.models.driver import Driver
        
        # Нормализуем номер телефона
        normalized_phone = normalize_phone_number(phoneNumber)
        print(f"Checking status for phone: {phoneNumber}")
        print(f"Normalized phone: {normalized_phone}")
        driver = db.query(Driver).filter(Driver.phone_number == normalized_phone).first()
        print(f"Found driver: {driver}")
        
        if driver:
            print(f"Driver is_active: {driver.is_active}")
            status_info = {
                "exists": True,
                "driver": {
                    "id": driver.id,
                    "phoneNumber": driver.phone_number,
                    "fullName": f"{driver.first_name} {driver.last_name}",
                    "status": "active" if driver.is_active else "inactive",
                    "registeredAt": driver.created_at.isoformat() if driver.created_at else None
                }
            }
            
            # Если водитель заблокирован или удален, добавляем информацию
            if not driver.is_active:
                status_info["driver"]["blocked"] = True
                status_info["driver"]["blockMessage"] = "Ваш аккаунт заблокирован суперадмином. Для связи: +996 559 868 878"
            
            print(f"Returning status info: {status_info}")
            return status_info
        else:
            print("Driver not found")
            return {
                "exists": False,
                "message": "Водитель не найден или удален суперадмином. Для связи: +996 559 868 878"
            }
            
    except Exception as e:
        print(f"Error in check_driver_status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check error: {str(e)}")


