import json
import os
from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.superadmin_service import SuperAdminService
from app.services.analytics_service import AnalyticsService
from app.services.taxipark_service import TaxiParkService
from app.services.administrator_service import AdministratorService
from app.schemas.superadmin import SuperAdminCreate, SuperAdminResponse
from app.schemas.taxipark import TaxiParkCreate, TaxiParkUpdate, TaxiParkList
from app.schemas.administrator import AdministratorCreate, AdministratorUpdate, AdministratorList
from typing import List, Optional

router = APIRouter(prefix="/superadmin", tags=["superadmin"])
templates = Jinja2Templates(directory="templates")

# Путь к JSON файлу с данными администраторов
ADMIN_DATA_FILE = "admin_data.json"

def save_admin_data_to_json(admin_data: dict):
    """Сохранить данные администратора в JSON файл"""
    try:
        # Загружаем существующие данные
        existing_data = []
        if os.path.exists(ADMIN_DATA_FILE):
            with open(ADMIN_DATA_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        
        # Добавляем нового администратора
        existing_data.append(admin_data)
        
        # Сохраняем обновленные данные
        with open(ADMIN_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"Ошибка сохранения в JSON: {e}")

def load_admin_data_from_json() -> List[dict]:
    """Загрузить данные администраторов из JSON файла"""
    try:
        if os.path.exists(ADMIN_DATA_FILE):
            with open(ADMIN_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Ошибка загрузки из JSON: {e}")
        return []

@router.get("/login", response_class=HTMLResponse)
async def superadmin_login_page(request: Request):
    return templates.TemplateResponse("superadmin/login.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
async def superadmin_dashboard_page(request: Request):
    return templates.TemplateResponse("superadmin/dashboard.html", {"request": request})

@router.get("/users", response_class=HTMLResponse)
async def superadmin_users_page(request: Request):
    return templates.TemplateResponse("superadmin/users.html", {"request": request})

@router.get("/drivers", response_class=HTMLResponse)
async def superadmin_drivers_page(request: Request):
    return templates.TemplateResponse("superadmin/drivers.html", {"request": request})

@router.get("/orders", response_class=HTMLResponse)
async def superadmin_orders_page(request: Request):
    return templates.TemplateResponse("superadmin/orders.html", {"request": request})

@router.get("/analytics", response_class=HTMLResponse)
async def superadmin_analytics_page(request: Request):
    return templates.TemplateResponse("superadmin/analytics.html", {"request": request})

@router.get("/settings", response_class=HTMLResponse)
async def superadmin_settings_page(request: Request):
    return templates.TemplateResponse("superadmin/settings.html", {"request": request})

@router.get("/taxiparks", response_class=HTMLResponse)
async def superadmin_taxiparks_page(request: Request):
    return templates.TemplateResponse("superadmin/taxiparks.html", {"request": request})

@router.get("/admins", response_class=HTMLResponse)
async def superadmin_admins_page(request: Request):
    return templates.TemplateResponse("superadmin/admins.html", {"request": request})

# API endpoints для получения данных
@router.get("/api/metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """Получить метрики для дашборда"""
    print("🚀 API METRICS: Начало выполнения")
    try:
        # Отладочная информация
        from app.models.order import Order
        from sqlalchemy import func
        
        print("🚀 API METRICS: Импорты выполнены")
        
        # Проверяем все заказы
        all_orders = db.query(Order).all()
        print(f"🚀 API METRICS: Все заказы из базы: {len(all_orders)}")
        for order in all_orders:
            print(f"  - ID: {order.id}, Статус: {order.status}, Цена: {order.price}")
        
        total_orders = db.query(Order).count()
        non_cancelled_orders = db.query(Order).filter(Order.status != "cancelled").count()
        total_earnings = db.query(Order).filter(Order.status != "cancelled").with_entities(func.sum(Order.price)).scalar() or 0.0
        
        print(f"🔍 DEBUG: Всего заказов в базе: {total_orders}")
        print(f"🔍 DEBUG: Не отмененных заказов: {non_cancelled_orders}")
        print(f"🔍 DEBUG: Общая сумма: {total_earnings}")
        
        # Временно используем прямые запросы вместо AnalyticsService
        stats = {
            "orders_completed": non_cancelled_orders,
            "total_earnings": total_earnings,
            "driver_topups": 2,  # Временно фиксированное значение
            "total_superadmins": 1,  # Временно фиксированное значение
            "period_days": 7
        }
        
        print(f"📊 METRICS: Получены метрики: {stats}")
        print(f"📊 METRICS: Типы данных:")
        for key, value in stats.items():
            print(f"  {key}: {value} (тип: {type(value)})")
        return stats
    except Exception as e:
        print(f"❌ METRICS: Ошибка при получении метрик: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении метрик: {str(e)}"
        )

@router.get("/api/superadmins", response_model=List[SuperAdminResponse])
async def get_superadmins_list(db: Session = Depends(get_db)):
    """Получить список всех суперадминов"""
    try:
        superadmins = SuperAdminService.get_superadmins(db)
        return superadmins
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка суперадминов: {str(e)}"
        )

@router.post("/api/superadmins", response_model=SuperAdminResponse)
async def create_superadmin(
    superadmin_data: SuperAdminCreate,
    db: Session = Depends(get_db)
):
    """Создать нового суперадмина"""
    try:
        new_superadmin = SuperAdminService.create_superadmin(db, superadmin_data)
        return new_superadmin
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании суперадмина: {str(e)}"
        )

# API endpoints для таксопарков
@router.get("/api/taxiparks", response_model=List[TaxiParkList])
async def get_taxiparks_list(db: Session = Depends(get_db)):
    """Получить список всех таксопарков"""
    try:
        from app.models.driver import Driver
        from app.models.administrator import Administrator
        
        taxiparks = TaxiParkService.get_taxiparks(db)
        
        # Подсчитываем реальное количество водителей и диспетчеров для каждого таксопарка
        taxiparks_with_counts = []
        for taxipark in taxiparks:
            # Подсчитываем водителей
            drivers_count = db.query(Driver).filter(Driver.taxipark_id == taxipark.id).count()
            
            # Подсчитываем диспетчеров (администраторов)
            dispatchers_count = db.query(Administrator).filter(Administrator.taxipark_id == taxipark.id).count()
            
            # Обновляем счетчики в объекте
            taxipark.drivers_count = drivers_count
            taxipark.dispatchers_count = dispatchers_count
            
            taxiparks_with_counts.append(taxipark)
        
        return taxiparks_with_counts
    except Exception as e:
        print(f"❌ ERROR: Ошибка при получении списка таксопарков: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка таксопарков: {str(e)}"
        )

@router.post("/api/taxiparks", response_model=TaxiParkList)
async def create_taxipark(
    taxipark_data: TaxiParkCreate,
    db: Session = Depends(get_db)
):
    """Создать новый таксопарк"""
    try:
        new_taxipark = TaxiParkService.create_taxipark(db, taxipark_data)
        return new_taxipark
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании таксопарка: {str(e)}"
        )

@router.put("/api/taxiparks/{taxipark_id}")
async def update_taxipark(
    taxipark_id: int,
    taxipark_data: dict,
    db: Session = Depends(get_db)
):
    """Обновить таксопарк"""
    try:
        update_data = {}
        if "is_active" in taxipark_data:
            update_data["is_active"] = taxipark_data["is_active"]
        if "name" in taxipark_data:
            update_data["name"] = taxipark_data["name"]
        if "commission_percent" in taxipark_data:
            update_data["commission_percent"] = taxipark_data["commission_percent"]
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не указаны данные для обновления"
            )
        
        updated_taxipark = TaxiParkService.update_taxipark(db, taxipark_id, TaxiParkUpdate(**update_data))
        if not updated_taxipark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Таксопарк не найден"
            )
        
        return {"message": "Таксопарк обновлен успешно", "taxipark": updated_taxipark}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении таксопарка: {str(e)}"
        )

@router.put("/api/taxiparks/{taxipark_id}/commission")
async def update_taxipark_commission(
    taxipark_id: int,
    commission_data: dict,
    db: Session = Depends(get_db)
):
    """Обновить процент комиссии таксопарка"""
    try:
        commission_percent = commission_data.get("commission_percent")
        if commission_percent is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не указан процент комиссии"
            )
        
        updated_taxipark = TaxiParkService.update_commission(db, taxipark_id, commission_percent)
        if not updated_taxipark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Таксопарк не найден"
            )
        
        return {"message": "Комиссия обновлена успешно", "taxipark": updated_taxipark}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении комиссии: {str(e)}"
        )

@router.delete("/api/taxiparks/{taxipark_id}")
async def delete_taxipark(
    taxipark_id: int,
    db: Session = Depends(get_db)
):
    """Удалить таксопарк"""
    try:
        success = TaxiParkService.delete_taxipark(db, taxipark_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Таксопарк не найден"
            )
        
        return {"message": "Таксопарк удален успешно"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении таксопарка: {str(e)}"
        )

# API endpoints для администраторов
@router.get("/api/administrators")
async def get_administrators_list(
    taxipark_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Получить список всех администраторов с возможностью фильтрации по таксопарку"""
    try:
        administrators = AdministratorService.get_administrators_with_taxipark_info(db, taxipark_id)
        return administrators
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка администраторов: {str(e)}"
        )

@router.post("/api/administrators")
async def create_administrator(
    administrator_data: AdministratorCreate,
    db: Session = Depends(get_db)
):
    """Создать нового администратора"""
    try:
        # Проверяем, существует ли таксопарк
        taxipark = TaxiParkService.get_taxipark(db, administrator_data.taxipark_id)
        if not taxipark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Таксопарк не найден"
            )
        
        # Создаем администратора
        new_administrator = AdministratorService.create_administrator(db, administrator_data)
        
        # Сохраняем данные в JSON файл
        admin_json_data = {
            "id": new_administrator.id,
            "login": administrator_data.login,
            "password": administrator_data.password,
            "first_name": administrator_data.first_name,
            "last_name": administrator_data.last_name,
            "taxipark_id": administrator_data.taxipark_id,
            "created_at": new_administrator.created_at.isoformat() if new_administrator.created_at else None
        }
        save_admin_data_to_json(admin_json_data)
        
        return {"message": "Администратор успешно создан", "administrator": new_administrator}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании администратора: {str(e)}"
        )

@router.put("/api/administrators/{administrator_id}/toggle-status")
async def toggle_administrator_status(
    administrator_id: int,
    db: Session = Depends(get_db)
):
    """Переключить статус администратора (заблокировать/разблокировать)"""
    try:
        updated_administrator = AdministratorService.toggle_administrator_status(db, administrator_id)
        if not updated_administrator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Администратор не найден"
            )
        
        action = "разблокирован" if updated_administrator.is_active else "заблокирован"
        return {"message": f"Администратор успешно {action}", "administrator": updated_administrator}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при изменении статуса администратора: {str(e)}"
        )

@router.delete("/api/administrators/{administrator_id}")
async def delete_administrator(
    administrator_id: int,
    db: Session = Depends(get_db)
):
    """Удалить администратора"""
    try:
        success = AdministratorService.delete_administrator(db, administrator_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Администратор не найден"
            )
        
        return {"message": "Администратор успешно удален"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении администратора: {str(e)}"
        )

@router.get("/api/administrators/count")
async def get_administrators_count(
    taxipark_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Получить количество администраторов с возможностью фильтрации по таксопарку"""
    try:
        count = AdministratorService.get_administrator_count(db, taxipark_id)
        return {"count": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении количества администраторов: {str(e)}"
        )

@router.get("/api/administrators/json-data")
async def get_administrators_json_data():
    """Получить данные администраторов из JSON файла (только создаваемые админы)"""
    try:
        admin_data = load_admin_data_from_json()
        return {"administrators": admin_data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении данных из JSON: {str(e)}"
        )

@router.get("/api/drivers")
async def get_drivers_list(db: Session = Depends(get_db)):
    """Получить список всех водителей"""
    try:
        from app.models.driver import Driver
        from app.models.taxipark import TaxiPark
        
        print(f"🔍 DEBUG: Запрос списка водителей")
        
        drivers = db.query(Driver).all()
        print(f"🔍 DEBUG: Найдено водителей: {len(drivers)}")
        
        drivers_data = []
        for driver in drivers:
            taxipark_name = "Не указан"
            if driver.taxipark_id:
                taxipark = db.query(TaxiPark).filter(TaxiPark.id == driver.taxipark_id).first()
                if taxipark:
                    taxipark_name = taxipark.name
            
            drivers_data.append({
                "id": driver.id,
                "first_name": driver.first_name,
                "last_name": driver.last_name,
                "phone_number": driver.phone_number,
                "car_model": driver.car_model,
                "car_number": driver.car_number,
                "balance": float(driver.balance) if driver.balance else 0.0,
                "tariff": driver.tariff,
                "taxipark_name": taxipark_name,
                "is_active": driver.is_active,
                "created_at": driver.created_at.isoformat() if driver.created_at else None,
                "updated_at": driver.updated_at.isoformat() if driver.updated_at else None
            })
        
        print(f"🔍 DEBUG: Подготовлено данных: {len(drivers_data)}")
        return {"drivers": drivers_data, "count": len(drivers_data)}
    except Exception as e:
        print(f"❌ ERROR: Ошибка при получении списка водителей: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка водителей: {str(e)}"
        )

@router.delete("/api/drivers/{driver_id}")
async def delete_driver(
    driver_id: int,
    reason: str,
    db: Session = Depends(get_db)
):
    """Удалить водителя с указанием причины"""
    try:
        from app.models.driver import Driver
        
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Водитель не найден"
            )
        
        # Сохраняем данные водителя перед удалением для мобильного приложения
        driver_data = {
            "id": driver.id,
            "first_name": driver.first_name,
            "last_name": driver.last_name,
            "phone_number": driver.phone_number,
            "deleted_reason": reason,
            "deleted_at": datetime.now().isoformat(),
            "contact_phone": "+996 559 868 878"
        }
        
        # В реальном приложении здесь можно сохранить в отдельную таблицу deleted_drivers
        # или отправить уведомление в мобильное приложение
        
        taxipark_id = driver.taxipark_id
        db.delete(driver)
        db.commit()
        
        # Обновляем счетчик водителей в таксопарке
        TaxiParkService.update_drivers_count(db, taxipark_id)
        
        print(f"🗑️ Водитель {driver.first_name} {driver.last_name} удален. Причина: {reason}")
        
        return {
            "message": "Водитель успешно удален",
            "driver_data": driver_data
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении водителя: {str(e)}"
        )

@router.put("/api/drivers/{driver_id}/block")
async def block_driver(
    driver_id: int,
    reason: str,
    db: Session = Depends(get_db)
):
    """Заблокировать водителя с указанием причины"""
    try:
        from app.models.driver import Driver
        from datetime import datetime
        
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Водитель не найден"
            )
        
        # Сохраняем данные блокировки для мобильного приложения
        block_data = {
            "id": driver.id,
            "first_name": driver.first_name,
            "last_name": driver.last_name,
            "phone_number": driver.phone_number,
            "block_reason": reason,
            "blocked_at": datetime.now().isoformat(),
            "contact_phone": "+996 559 868 878"
        }
        
        driver.is_active = False
        db.commit()
        db.refresh(driver)
        
        print(f"🚫 Водитель {driver.first_name} {driver.last_name} заблокирован. Причина: {reason}")
        
        return {
            "message": "Водитель успешно заблокирован",
            "driver_data": block_data
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при блокировке водителя: {str(e)}"
        )

@router.put("/api/drivers/{driver_id}/unblock")
async def unblock_driver(
    driver_id: int,
    db: Session = Depends(get_db)
):
    """Разблокировать водителя"""
    try:
        from app.models.driver import Driver
        
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Водитель не найден"
            )
        
        driver.is_active = True
        db.commit()
        db.refresh(driver)
        
        print(f"✅ Водитель {driver.first_name} {driver.last_name} разблокирован")
        
        return {
            "message": "Водитель успешно разблокирован",
            "driver": {
                "id": driver.id,
                "first_name": driver.first_name,
                "last_name": driver.last_name,
                "is_active": driver.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при разблокировке водителя: {str(e)}"
        )

@router.get("/api/drivers/stats")
async def get_drivers_stats(db: Session = Depends(get_db)):
    """Получить статистику по водителям"""
    try:
        stats = AnalyticsService.get_drivers_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении статистики водителей: {str(e)}"
        )

@router.get("/api/orders/stats")
async def get_orders_stats(db: Session = Depends(get_db)):
    """Получить статистику по заказам"""
    try:
        stats = AnalyticsService.get_orders_stats(db, days=7)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении статистики заказов: {str(e)}"
        )

# API endpoints для клиентов
@router.get("/api/clients")
async def get_clients_list(db: Session = Depends(get_db)):
    """Получить список всех клиентов"""
    try:
        from app.models.client import Client
        
        print(f"🔍 DEBUG: Запрос списка клиентов")
        
        clients = db.query(Client).all()
        print(f"🔍 DEBUG: Найдено клиентов: {len(clients)}")
        
        clients_data = []
        for client in clients:
            clients_data.append({
                "id": client.id,
                "first_name": client.first_name,
                "last_name": client.last_name,
                "phone_number": client.phone_number,
                "email": client.email,
                "rating": float(client.rating) if client.rating else 5.0,
                "total_rides": client.total_rides,
                "total_spent": float(client.total_spent) if client.total_spent else 0.0,
                "preferred_payment_method": client.preferred_payment_method,
                "is_active": client.is_active,
                "created_at": client.created_at.isoformat() if client.created_at else None,
                "updated_at": client.updated_at.isoformat() if client.updated_at else None
            })
        
        print(f"🔍 DEBUG: Подготовлено данных клиентов: {len(clients_data)}")
        return {"clients": clients_data, "count": len(clients_data)}
    except Exception as e:
        print(f"❌ ERROR: Ошибка при получении списка клиентов: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка клиентов: {str(e)}"
        )

@router.put("/api/clients/{client_id}/toggle-status")
async def toggle_client_status(
    client_id: int,
    db: Session = Depends(get_db)
):
    """Переключить статус клиента (заблокировать/разблокировать)"""
    try:
        from app.models.client import Client
        
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Клиент не найден"
            )
        
        client.is_active = not client.is_active
        db.commit()
        db.refresh(client)
        
        action = "разблокирован" if client.is_active else "заблокирован"
        print(f"👤 Клиент {client.first_name} {client.last_name} {action}")
        
        return {
            "message": f"Клиент успешно {action}",
            "client": {
                "id": client.id,
                "first_name": client.first_name,
                "last_name": client.last_name,
                "is_active": client.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при изменении статуса клиента: {str(e)}"
        )

# API endpoint для аналитики
@router.get("/api/analytics")
async def get_analytics_data(
    period: int = 7,
    db: Session = Depends(get_db)
):
    """Получить аналитические данные"""
    try:
        from app.models.order import Order
        from app.models.driver import Driver
        from app.models.client import Client
        from sqlalchemy import func, and_
        from datetime import datetime, timedelta
        
        print(f"📊 ANALYTICS: Запрос аналитики за {period} дней")
        
        # Дата начала периода
        start_date = datetime.now() - timedelta(days=period)
        
        # Основные метрики
        total_orders = db.query(Order).filter(Order.status != "cancelled").count()
        total_revenue = db.query(Order).filter(Order.status != "cancelled").with_entities(func.sum(Order.price)).scalar() or 0.0
        active_drivers = db.query(Driver).filter(Driver.is_active == True).count()
        average_order = total_revenue / total_orders if total_orders > 0 else 0.0
        
        # Статистика по статусам заказов
        orders_by_status = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
        orders_status_dict = dict(orders_by_status)
        
        # Топ водители (по количеству заказов)
        top_drivers_query = db.query(
            Driver.first_name,
            Driver.last_name,
            func.count(Order.id).label('orders_count'),
            func.sum(Order.price).label('total_revenue')
        ).join(Order, Driver.id == Order.driver_id).filter(
            Order.status == "completed"
        ).group_by(Driver.id, Driver.first_name, Driver.last_name).order_by(
            func.count(Order.id).desc()
        ).limit(5).all()
        
        top_drivers = [
            {
                "name": f"{driver.first_name} {driver.last_name}",
                "orders": driver.orders_count,
                "revenue": float(driver.total_revenue) if driver.total_revenue else 0.0
            }
            for driver in top_drivers_query
        ]
        
        # Данные для графика доходов (пока пустые, будут реальные данные)
        revenue_data = []
        
        analytics_data = {
            "total_revenue": float(total_revenue),
            "total_orders": total_orders,
            "active_drivers": active_drivers,
            "average_order": float(average_order),
            "orders_by_status": {
                "completed": orders_status_dict.get("completed", 0),
                "cancelled": orders_status_dict.get("cancelled", 0),
                "in_progress": orders_status_dict.get("in_progress", 0),
                "pending": orders_status_dict.get("pending", 0)
            },
            "top_drivers": top_drivers,
            "revenue_data": revenue_data,
            "period_days": period
        }
        
        print(f"📊 ANALYTICS: Подготовлены данные аналитики")
        print(f"  - Общий доход: {total_revenue}")
        print(f"  - Заказов: {total_orders}")
        print(f"  - Активных водителей: {active_drivers}")
        print(f"  - Средний чек: {average_order}")
        
        return analytics_data
        
    except Exception as e:
        print(f"❌ ANALYTICS: Ошибка при получении аналитики: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении аналитических данных: {str(e)}"
        )
