from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.driver import Driver
from app.models.taxipark import TaxiPark
from app.models.order import Order
from typing import Optional
from datetime import datetime, timedelta

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

@router.get("/api/drivers/profile")
async def get_driver_profile(
    phoneNumber: str = Query(..., description="Номер телефона водителя"),
    db: Session = Depends(get_db)
):
    """Получить профиль водителя"""
    try:
        print(f"🚗 Getting driver profile: {phoneNumber}")
        
        # Нормализуем номер к единому формату БД
        normalized_phone = normalize_phone_number(phoneNumber)
        print(f"🚗 Normalized phone: '{normalized_phone}'")
        
        if not normalized_phone:
            raise HTTPException(status_code=400, detail="Некорректный номер телефона")
        
        # Ищем водителя по нормализованному номеру
        driver = db.query(Driver).filter(Driver.phone_number == normalized_phone).first()
        
        if not driver:
            raise HTTPException(status_code=404, detail="Водитель не найден")
        
        # Получаем информацию о таксопарке
        taxipark = db.query(TaxiPark).filter(TaxiPark.id == driver.taxipark_id).first()
        
        profile_data = {
            "id": driver.id,
            "first_name": driver.first_name,
            "last_name": driver.last_name,
            "phone_number": driver.phone_number,
            "car_model": driver.car_model,
            "car_number": driver.car_number,
            "car_color": driver.car_color,
            "car_year": driver.car_year,
            "car_vin": driver.car_vin,
            "car_body_number": driver.car_body_number,
            "car_sts": driver.car_sts,
            "call_sign": driver.call_sign,
            "balance": float(driver.balance) if driver.balance else 0.0,
            "tariff": driver.tariff,
            "is_active": driver.is_active,
            "taxipark": {
                "id": taxipark.id if taxipark else None,
                "name": taxipark.name if taxipark else "Не указано",
                "commission": float(taxipark.commission_percent) if taxipark and taxipark.commission_percent else 0.0,
            } if taxipark else None,
            "created_at": driver.created_at.isoformat() if driver.created_at else None,
            "updated_at": driver.updated_at.isoformat() if driver.updated_at else None
        }
        
        print(f"🚗 Profile data: {profile_data}")
        return profile_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"🚗 Error getting driver profile: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения профиля: {str(e)}")

@router.get("/api/drivers/car")
async def get_driver_car(
    phoneNumber: str = Query(..., description="Номер телефона водителя"),
    db: Session = Depends(get_db)
):
    """Получить информацию об автомобиле водителя"""
    try:
        print(f"🚗 Getting car info: {phoneNumber}")
        
        # Нормализуем номер к единому формату БД
        normalized_phone = normalize_phone_number(phoneNumber)
        
        if not normalized_phone:
            raise HTTPException(status_code=400, detail="Некорректный номер телефона")
        
        # Ищем водителя по нормализованному номеру
        driver = db.query(Driver).filter(Driver.phone_number == normalized_phone).first()
        
        if not driver:
            raise HTTPException(status_code=404, detail="Водитель не найден")
        
        car_data = {
            "id": driver.id,
            "car_model": driver.car_model,
            "car_number": driver.car_number,
            "car_color": driver.car_color,
            "car_year": driver.car_year,
            "car_vin": driver.car_vin,
            "car_body_number": driver.car_body_number,
            "car_sts": driver.car_sts,
            "is_primary": True  # Пока всегда основная машина
        }
        
        print(f"🚗 Car data: {car_data}")
        return car_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"🚗 Error getting car info: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации об автомобиле: {str(e)}")

@router.get("/api/drivers/taxipark")
async def get_driver_taxipark(
    phoneNumber: str = Query(..., description="Номер телефона водителя"),
    db: Session = Depends(get_db)
):
    """Получить информацию о таксопарке водителя"""
    try:
        print(f"🏢 Getting taxipark info: {phoneNumber}")
        
        # Нормализуем номер к единому формату БД
        normalized_phone = normalize_phone_number(phoneNumber)
        
        if not normalized_phone:
            raise HTTPException(status_code=400, detail="Некорректный номер телефона")
        
        # Ищем водителя по нормализованному номеру
        driver = db.query(Driver).filter(Driver.phone_number == normalized_phone).first()
        
        if not driver:
            raise HTTPException(status_code=404, detail="Водитель не найден")
        
        # Получаем информацию о таксопарке
        taxipark = db.query(TaxiPark).filter(TaxiPark.id == driver.taxipark_id).first()
        
        if not taxipark:
            raise HTTPException(status_code=404, detail="Таксопарк не найден")
        
        taxipark_data = {
            "id": taxipark.id,
            "name": taxipark.name,
            "commission": float(taxipark.commission_percent) if taxipark.commission_percent else 0.0,
            "phone": taxipark.phone or "+970667788778",
            "email": taxipark.email or "Example@gmail.com",
            "address": taxipark.address or "Кыргыстан г. Ок мкр Анар 1, (орентир Автомойка Нурзаман, кафе Нирвана)",
            "work_schedule": taxipark.working_hours or "Пн-Сб 10:00-18:00\nВс-выходной",
            "is_selected": True
        }
        
        print(f"🏢 Taxipark data: {taxipark_data}")
        return taxipark_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"🏢 Error getting taxipark info: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации о таксопарке: {str(e)}")

@router.get("/api/drivers/weekly-results")
async def get_weekly_results(
    phoneNumber: str = Query(..., description="Номер телефона водителя"),
    db: Session = Depends(get_db)
):
    """Получить результаты недели водителя"""
    try:
        print(f"📊 Getting weekly results: {phoneNumber}")
        
        # Нормализуем номер к единому формату БД
        normalized_phone = normalize_phone_number(phoneNumber)
        
        if not normalized_phone:
            raise HTTPException(status_code=400, detail="Некорректный номер телефона")
        
        # Ищем водителя по нормализованному номеру
        driver = db.query(Driver).filter(Driver.phone_number == normalized_phone).first()
        
        if not driver:
            raise HTTPException(status_code=404, detail="Водитель не найден")
        
        # Получаем заказы за последнюю неделю
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        
        weekly_orders = db.query(Order).filter(
            Order.driver_id == driver.id,
            Order.created_at >= week_ago,
            Order.status == 'completed'
        ).count()
        
        # Получаем общую статистику
        total_orders = db.query(Order).filter(
            Order.driver_id == driver.id,
            Order.status == 'completed'
        ).count()
        
        results_data = {
            "driver_id": driver.id,
            "weekly_orders": weekly_orders,
            "total_orders": total_orders,
            "target_orders": 10,
            "has_achieved_goal": weekly_orders >= 10,
            "week_start": week_ago.isoformat(),
            "week_end": now.isoformat(),
            "reviews": [
                "Отличный водитель, вежливый и пунктуальный",
                "Быстрая и комфортная поездка",
                "Рекомендую этого водителя"
            ] if weekly_orders >= 10 else [],
            "observations": {
                "rating": 4.9,
                "average_wait_time": "3 минуты",
                "completion_rate": "100%"
            } if weekly_orders >= 10 else {}
        }
        
        print(f"📊 Weekly results: {results_data}")
        return results_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"📊 Error getting weekly results: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения результатов недели: {str(e)}")
