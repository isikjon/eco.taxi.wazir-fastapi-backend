from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientLogin
import sqlite3
import os
from datetime import datetime

client_router = APIRouter(prefix="/api/clients", tags=["client-api"])

# Путь к базе данных для SMS
DB_PATH = "taxi_admin.db"

def get_db_connection():
    if not os.path.exists(DB_PATH):
        return None
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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

@client_router.post("/register")
async def register_client(client_data: ClientCreate, db: Session = Depends(get_db)):
    """Регистрация нового клиента"""
    try:
        # Нормализуем номер телефона
        normalized_phone = normalize_phone_number(client_data.phone_number)
        
        # Проверяем, существует ли клиент с таким номером
        existing_client = db.query(Client).filter(Client.phone_number == normalized_phone).first()
        
        if existing_client:
            return {
                "success": False,
                "error": "Клиент с таким номером уже существует"
            }
        
        # Создаем нового клиента
        new_client = Client(
            first_name=client_data.first_name,
            last_name=client_data.last_name,
            phone_number=normalized_phone,
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
        # Нормализуем номер телефона
        normalized_phone = normalize_phone_number(login_data.phone_number)
        
        # Проверяем SMS код в SQLite БД
        conn = get_db_connection()
        if not conn:
            return {
                "success": False,
                "error": "База данных SMS недоступна"
            }
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM sms_codes 
            WHERE phone_number = ? AND code = ? AND used = FALSE 
            AND datetime('now') < expires_at
            ORDER BY created_at DESC LIMIT 1
        ''', (normalized_phone, login_data.sms_code))
        
        sms_record = cursor.fetchone()
        if not sms_record:
            conn.close()
            return {
                "success": False,
                "error": "Неверный или истекший SMS код"
            }
        
        # Отмечаем код как использованный
        cursor.execute('''
            UPDATE sms_codes SET used = TRUE WHERE id = ?
        ''', (sms_record['id'],))
        conn.commit()
        conn.close()
        
        # Ищем клиента по номеру телефона
        client = db.query(Client).filter(Client.phone_number == normalized_phone).first()
        
        if not client:
            return {
                "success": True,
                "isNewUser": True,
                "message": "Новый пользователь, требуется регистрация"
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
        normalized_phone = normalize_phone_number(phone_number)
        client = db.query(Client).filter(Client.phone_number == normalized_phone).first()
        
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

@client_router.put("/update")
async def update_client_profile(update_data: dict, db: Session = Depends(get_db)):
    """Обновление профиля клиента"""
    try:
        # Получаем данные из запроса
        first_name = update_data.get('first_name')
        last_name = update_data.get('last_name')
        
        if not first_name or not last_name:
            return {
                "success": False,
                "error": "Имя и фамилия обязательны"
            }
        
        # Ищем клиента по ID (нужно будет передавать ID клиента)
        # Пока что обновляем первого найденного клиента для тестирования
        client = db.query(Client).first()
        
        if not client:
            return {
                "success": False,
                "error": "Клиент не найден"
            }
        
        # Обновляем данные
        client.first_name = first_name
        client.last_name = last_name
        client.updated_at = datetime.now()
        
        db.commit()
        db.refresh(client)
        
        return {
            "success": True,
            "data": {
                "client": client.to_dict(),
                "message": "Профиль успешно обновлен"
            }
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"Ошибка обновления профиля: {str(e)}"
        }

@client_router.put("/update-payment-method")
async def update_client_payment_method(update_data: dict, db: Session = Depends(get_db)):
    """Обновление способа оплаты клиента"""
    try:
        # Получаем данные из запроса
        client_id = update_data.get('client_id')
        payment_method = update_data.get('payment_method')
        
        if not client_id or not payment_method:
            return {
                "success": False,
                "error": "ID клиента и способ оплаты обязательны"
            }
        
        # Ищем клиента по ID
        client = db.query(Client).filter(Client.id == client_id).first()
        
        if not client:
            return {
                "success": False,
                "error": "Клиент не найден"
            }
        
        # Обновляем способ оплаты
        client.preferred_payment_method = payment_method
        client.updated_at = datetime.now()
        
        db.commit()
        db.refresh(client)
        
        return {
            "success": True,
            "data": {
                "client": client.to_dict(),
                "message": "Способ оплаты успешно обновлен"
            }
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"Ошибка обновления способа оплаты: {str(e)}"
        }