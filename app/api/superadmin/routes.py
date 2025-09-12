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
    try:
        stats = AnalyticsService.get_dashboard_stats(db, days=7)
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
