from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import json
import hashlib
import uuid
from datetime import datetime
import os

# Импорт роутеров
from app.api.auth.routes import router as auth_router
from app.api.dispatcher.routes import router as dispatcher_router  
from app.api.superadmin.routes import router as superadmin_router
from app.database.session import get_db, SessionLocal
from app.middleware.dispatcher_auth import check_dispatcher_auth

app = FastAPI(title="Taxi Driver Registration API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dispatcher authentication middleware
app.middleware("http")(check_dispatcher_auth)

# Настройка статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройка шаблонов
templates = Jinja2Templates(directory="templates")

# Подключение роутеров
app.include_router(auth_router)
app.include_router(dispatcher_router)  
app.include_router(superadmin_router)

# Путь к базе данных
DB_PATH = "taxi_admin.db"

# API для обновления статуса заказа водителем
@app.put("/api/orders/{order_id}/status")
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
@app.on_event("startup")
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
    """Нормализует номер телефона к единому формату +996XXXXXXXXX для поиска в БД"""
    if not phone_number:
        return None
    
    # Извлекаем только цифры из номера
    digits_only = ''.join(filter(str.isdigit, phone_number))
    
    # Если номер начинается с 996, добавляем +
    if digits_only.startswith('996'):
        return f"+{digits_only}"
    
    # Если номер начинается с 9 (без 996), добавляем +996
    if digits_only.startswith('9') and len(digits_only) == 9:
        return f"+996{digits_only}"
    
    # Если номер уже содержит 996 в начале, просто добавляем +
    if len(digits_only) >= 12 and digits_only.startswith('996'):
        return f"+{digits_only}"
    
    return phone_number

# API endpoints

@app.get("/")
async def root():
    return {"message": "Taxi Driver Registration API", "version": "1.0.0"}

@app.get("/api/parks")
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

@app.post("/api/sms/send")
async def send_sms_code(request: SmsRequest):
    """Отправить SMS код (в тестовом режиме всегда возвращает успех)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # В реальном приложении здесь была бы интеграция с SMS сервисом
        # Для тестирования используем код 1111
        test_code = "1111"
        expires_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Сохраняем код в БД
        cursor.execute('''
            INSERT INTO sms_codes (phone_number, code, expires_at)
            VALUES (?, ?, datetime('now', '+10 minutes'))
        ''', (request.phoneNumber, test_code))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "SMS код отправлен",
            "test_code": test_code  # В продакшене убрать
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMS sending error: {str(e)}")

@app.post("/api/drivers/login")
async def login_driver(request: DriverLogin, db: SessionLocal = Depends(get_db)):
    """Авторизация водителя по номеру телефона и SMS коду"""
    try:
        from app.models.driver import Driver
        
        # Проверяем SMS код в SQLite БД
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM sms_codes 
            WHERE phone_number = ? AND code = ? AND used = FALSE 
            AND datetime('now') < expires_at
            ORDER BY created_at DESC LIMIT 1
        ''', (request.phoneNumber, request.smsCode))
        
        sms_record = cursor.fetchone()
        if not sms_record:
            conn.close()
            raise HTTPException(status_code=400, detail="Неверный или истекший SMS код")
        
        # Отмечаем код как использованный
        cursor.execute('''
            UPDATE sms_codes SET used = TRUE WHERE id = ?
        ''', (sms_record['id'],))
        conn.commit()
        conn.close()
        
        # Нормализуем номер телефона для поиска в БД
        normalized_phone = normalize_phone_number(request.phoneNumber)
        print(f"🔑 Original phone: {request.phoneNumber}")
        print(f"🔑 Normalized phone: {normalized_phone}")
        
        # Проверяем, существует ли водитель в SQLAlchemy БД
        driver = db.query(Driver).filter(Driver.phone_number == normalized_phone).first()
        
        if driver:
            # Существующий водитель
            print(f"Found driver: {driver}")
            print(f"Driver taxipark: {driver.taxipark}")
            
            try:
                taxipark_name = driver.taxipark.name if driver.taxipark else "Не указан"
            except Exception as e:
                print(f"Error getting taxipark name: {e}")
                taxipark_name = "Не указан"
            
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
            
            print(f"Returning driver data: {driver_data}")
            
            return {
                "success": True,
                "isNewUser": False,
                "driver": driver_data
            }
        else:
            # Новый водитель
            return {
                "success": True,
                "isNewUser": True,
                "message": "Новый пользователь, требуется регистрация"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@app.post("/api/drivers/register")
async def register_driver(registration: DriverRegistration, db: SessionLocal = Depends(get_db)):
    """Регистрация нового водителя"""
    try:
        from app.models.driver import Driver
        from app.models.taxipark import TaxiPark
        
        user_data = registration.user
        car_data = registration.car
        park_data = registration.park
        
        # Нормализуем номер телефона
        normalized_phone = normalize_phone_number(user_data.get('phoneNumber', ''))
        
        # Проверяем, не существует ли уже водитель с таким номером
        existing_driver = db.query(Driver).filter(Driver.phone_number == normalized_phone).first()
        if existing_driver:
            raise HTTPException(status_code=400, detail="Водитель с таким номером уже зарегистрирован")
        
        # Проверяем, существует ли таксопарк
        taxipark = db.query(TaxiPark).filter(TaxiPark.id == park_data.get('id')).first()
        if not taxipark:
            raise HTTPException(status_code=400, detail="Указанный таксопарк не найден")
        
        # Парсим полное имя
        full_name = user_data.get('fullName', '')
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0] if len(name_parts) > 0 else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Регистрируем нового водителя
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
        
        db.add(new_driver)
        db.commit()
        db.refresh(new_driver)
        
        # Обновляем счетчик водителей в таксопарке
        from app.services.taxipark_service import TaxiParkService
        TaxiParkService.update_drivers_count(db, new_driver.taxipark_id)
        
        return {
            "success": True,
            "message": "Водитель успешно зарегистрирован",
            "driver_id": new_driver.id,
            "status": "registered"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")

@app.get("/api/drivers/status")
async def check_driver_status(phoneNumber: str, db: SessionLocal = Depends(get_db)):
    """Проверить статус водителя"""
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081, reload=True)


# =============== CLIENT API ENDPOINTS ===============

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientLogin
import random
import string

client_router = APIRouter(prefix="/api/clients", tags=["client-api"])

@client_router.post("/register")
async def register_client(client_data: ClientCreate, db: Session = Depends(get_db)):
    """Регистрация нового клиента"""
    try:
        # Проверяем, существует ли клиент с таким номером
        existing_client = db.query(Client).filter(Client.phone_number == client_data.phone_number).first()
        
        if existing_client:
            return {
                "success": False,
                "error": "Клиент с таким номером уже существует"
            }
        
        # Создаем нового клиента
        new_client = Client(
            first_name=client_data.first_name,
            last_name=client_data.last_name,
            phone_number=client_data.phone_number,
            email=client_data.email,
            preferred_payment_method=client_data.preferred_payment_method or "cash"
        )
        
        db.add(new_client)
        db.commit()
        db.refresh(new_client)
        
        return {
            "success": True,
            "data": {
                "client": new_client.to_dict(),
                "message": "Клиент успешно зарегистрирован"
            }
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"Ошибка регистрации: {str(e)}"
        }

@client_router.post("/login")
async def login_client(login_data: ClientLogin, db: Session = Depends(get_db)):
    """Авторизация клиента"""
    try:
        # Ищем клиента по номеру телефона
        client = db.query(Client).filter(Client.phone_number == login_data.phone_number).first()
        
        if not client:
            return {
                "success": False,
                "error": "Клиент не найден"
            }
        
        # Проверяем статус клиента
        if not client.is_active:
            return {
                "success": False,
                "error": "blocked",
                "message": "Ваш аккаунт заблокирован. Обратитесь в поддержку."
            }
        
        return {
            "success": True,
            "data": {
                "client": client.to_dict(),
                "isNewUser": False
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Ошибка авторизации: {str(e)}"
        }

@client_router.get("/status")
async def get_client_status(phone_number: str, db: Session = Depends(get_db)):
    """Проверка статуса клиента"""
    try:
        client = db.query(Client).filter(Client.phone_number == phone_number).first()
        
        if not client:
            return {
                "success": False,
                "error": "Клиент не найден"
            }
        
        return {
            "success": True,
            "data": {
                "client": client.to_dict()
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Ошибка проверки статуса: {str(e)}"
        }

# =============== END CLIENT API ENDPOINTS ===============
