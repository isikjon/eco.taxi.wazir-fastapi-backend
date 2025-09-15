from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.driver import Driver
from app.models.order import Order
from app.models.transaction import DriverTransaction
from typing import Optional, List
from datetime import datetime, timedelta
import json

router = APIRouter()

def normalize_phone_number(phone_number):
    """Нормализует номер телефона к единому формату +996XXXXXXXXX для поиска в БД"""
    if not phone_number:
        return None
    
    # Извлекаем только цифры из номера
    digits_only = ''.join(filter(str.isdigit, phone_number))
    
    # Определяем основные 9 цифр номера
    if len(digits_only) >= 9:
        if digits_only.startswith('996') and len(digits_only) >= 12:
            # Номер с кодом страны 996
            main_digits = digits_only[3:12]  # Берем 9 цифр после 996
        else:
            # Берем последние 9 цифр
            main_digits = digits_only[-9:]
    else:
        return None  # Не можем нормализовать
    
    # Возвращаем в едином формате БД: +996XXXXXXXXX
    return f"+996{main_digits}"

@router.get("/api/drivers/balance")
async def get_driver_balance(
    phoneNumber: str = Query(..., description="Номер телефона водителя"),
    db: Session = Depends(get_db)
):
    """Получить баланс водителя"""
    try:
        print(f"💰 Getting balance for driver: {phoneNumber}")
        
        # Нормализуем номер к единому формату БД
        normalized_phone = normalize_phone_number(phoneNumber)
        print(f"💰 Normalized phone: '{normalized_phone}'")
        
        if not normalized_phone:
            raise HTTPException(status_code=400, detail="Некорректный номер телефона")
        
        # Ищем водителя по нормализованному номеру
        driver = db.query(Driver).filter(Driver.phone_number == normalized_phone).first()
        
        if not driver:
            # Выводим все номера в базе для отладки
            all_drivers = db.query(Driver).all()
            print(f"💰 All drivers in DB:")
            for d in all_drivers:
                print(f"  - ID: {d.id}, Phone: '{d.phone_number}', Name: {d.first_name} {d.last_name}")
            raise HTTPException(status_code=404, detail=f"Водитель не найден. Искали: '{normalized_phone}'")
        
        # Получаем статистику за неделю и месяц
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Подсчитываем заказы за неделю
        weekly_orders = db.query(Order).filter(
            Order.driver_id == driver.id,
            Order.created_at >= week_ago,
            Order.status == 'completed'
        ).count()
        
        # Подсчитываем заказы за месяц
        monthly_orders = db.query(Order).filter(
            Order.driver_id == driver.id,
            Order.created_at >= month_ago,
            Order.status == 'completed'
        ).count()
        
        # Подсчитываем общее количество заказов
        total_orders = db.query(Order).filter(
            Order.driver_id == driver.id,
            Order.status == 'completed'
        ).count()
        
        # Вычисляем заработки (примерная логика)
        weekly_earnings = weekly_orders * 150  # Примерно 150 сом за заказ
        monthly_earnings = monthly_orders * 150
        
        balance_data = {
            "balance": float(driver.balance) if driver.balance else 0.0,
            "weekly_earnings": weekly_earnings,
            "monthly_earnings": monthly_earnings,
            "total_orders": total_orders,
            "last_updated": now.isoformat(),
            "driver_id": driver.id,
            "phone_number": driver.phone_number
        }
        
        print(f"💰 Balance data: {balance_data}")
        return balance_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"💰 Error getting balance: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения баланса: {str(e)}")

@router.get("/api/drivers/transactions")
async def get_driver_transactions(
    phoneNumber: str = Query(..., description="Номер телефона водителя"),
    filter: str = Query("all", description="Фильтр: all, week, month"),
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(20, description="Количество записей на странице"),
    db: Session = Depends(get_db)
):
    """Получить транзакции водителя"""
    try:
        print(f"📊 Getting transactions for driver: {phoneNumber}, filter: {filter}")
        
        # Нормализуем номер к единому формату БД
        normalized_phone = normalize_phone_number(phoneNumber)
        print(f"📊 Normalized phone: '{normalized_phone}'")
        
        if not normalized_phone:
            raise HTTPException(status_code=400, detail="Некорректный номер телефона")
        
        # Ищем водителя по нормализованному номеру
        driver = db.query(Driver).filter(Driver.phone_number == normalized_phone).first()
        
        if not driver:
            raise HTTPException(status_code=404, detail="Водитель не найден")
        
        # Базовый запрос транзакций (РЕАЛЬНЫЕ ДАННЫЕ ТОЛЬКО!)
        query = db.query(DriverTransaction).filter(DriverTransaction.driver_id == driver.id)
        
        # Применяем фильтр по времени
        now = datetime.now()
        if filter == "week":
            week_ago = now - timedelta(days=7)
            query = query.filter(DriverTransaction.created_at >= week_ago)
        elif filter == "month":
            month_ago = now - timedelta(days=30)
            query = query.filter(DriverTransaction.created_at >= month_ago)
        
        # Получаем общее количество
        total_count = query.count()
        
        # Применяем пагинацию
        offset = (page - 1) * limit
        db_transactions = query.order_by(DriverTransaction.created_at.desc()).offset(offset).limit(limit).all()
        
        # Преобразуем в формат API
        transactions = []
        for trans in db_transactions:
            transaction = {
                "id": str(trans.id),
                "type": trans.type,
                "amount": float(trans.amount),
                "description": trans.description or "",
                "created_at": trans.created_at.isoformat() if trans.created_at else now.isoformat(),
                "status": trans.status or "completed",
                "reference": trans.reference or f"{trans.type.upper()}-{trans.id}"
            }
            transactions.append(transaction)
        
        # Вычисляем пагинацию
        total_pages = (total_count + limit - 1) // limit
        has_more = page < total_pages
        
        result = {
            "transactions": transactions,
            "total_count": total_count,
            "current_page": page,
            "total_pages": total_pages,
            "has_more": has_more,
            "filter": filter
        }
        
        print(f"📊 Transactions result: {len(transactions)} transactions found")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"📊 Error getting transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения транзакций: {str(e)}")

@router.get("/api/drivers/stats")
async def get_driver_stats(
    phoneNumber: str = Query(..., description="Номер телефона водителя"),
    db: Session = Depends(get_db)
):
    """Получить статистику водителя"""
    try:
        print(f"📈 Getting stats for driver: {phoneNumber}")
        
        # Нормализуем номер к единому формату БД
        normalized_phone = normalize_phone_number(phoneNumber)
        print(f"📈 Normalized phone: '{normalized_phone}'")
        
        if not normalized_phone:
            raise HTTPException(status_code=400, detail="Некорректный номер телефона")
        
        # Ищем водителя по нормализованному номеру
        driver = db.query(Driver).filter(Driver.phone_number == normalized_phone).first()
        
        if not driver:
            raise HTTPException(status_code=404, detail="Водитель не найден")
        
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Статистика заказов
        total_orders = db.query(Order).filter(Order.driver_id == driver.id).count()
        completed_orders = db.query(Order).filter(
            Order.driver_id == driver.id,
            Order.status == 'completed'
        ).count()
        cancelled_orders = db.query(Order).filter(
            Order.driver_id == driver.id,
            Order.status == 'cancelled'
        ).count()
        
        # Заработки
        weekly_orders = db.query(Order).filter(
            Order.driver_id == driver.id,
            Order.created_at >= week_ago,
            Order.status == 'completed'
        ).count()
        
        monthly_orders = db.query(Order).filter(
            Order.driver_id == driver.id,
            Order.created_at >= month_ago,
            Order.status == 'completed'
        ).count()
        
        total_earnings = completed_orders * 150  # Примерно 150 сом за заказ
        weekly_earnings = weekly_orders * 150
        monthly_earnings = monthly_orders * 150
        average_order_value = 150.0  # Примерное значение
        
        stats = {
            "total_earnings": total_earnings,
            "weekly_earnings": weekly_earnings,
            "monthly_earnings": monthly_earnings,
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
            "average_order_value": average_order_value,
            "rating": 5.0,  # Примерный рейтинг
            "total_rides": completed_orders,
            "driver_id": driver.id
        }
        
        print(f"📈 Stats data: {stats}")
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"📈 Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")

@router.post("/api/drivers/balance/topup")
async def request_balance_topup(
    request_data: dict,
    db: Session = Depends(get_db)
):
    """Запрос пополнения баланса"""
    try:
        phone_number = request_data.get("phoneNumber")
        amount = request_data.get("amount")
        
        if not phone_number or not amount:
            raise HTTPException(status_code=400, detail="Отсутствуют обязательные поля")
        
        print(f"💳 Balance topup request: {phone_number}, amount: {amount}")
        
        # Нормализуем номер к единому формату БД
        normalized_phone = normalize_phone_number(phone_number)
        print(f"💳 Normalized phone: '{normalized_phone}'")
        
        if not normalized_phone:
            raise HTTPException(status_code=400, detail="Некорректный номер телефона")
        
        # Ищем водителя по нормализованному номеру
        driver = db.query(Driver).filter(Driver.phone_number == normalized_phone).first()
        
        if not driver:
            raise HTTPException(status_code=404, detail="Водитель не найден")
        
        # В реальном приложении здесь была бы логика обработки платежа
        # Пока просто возвращаем успешный ответ
        
        result = {
            "success": True,
            "message": "Запрос на пополнение баланса принят",
            "amount": amount,
            "driver_id": driver.id,
            "request_id": f"TOPUP-{driver.id}-{int(datetime.now().timestamp())}"
        }
        
        print(f"💳 Topup result: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"💳 Error processing topup: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки запроса: {str(e)}")
