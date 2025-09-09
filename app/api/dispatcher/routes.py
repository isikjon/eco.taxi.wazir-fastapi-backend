from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.administrator_service import AdministratorService
from app.core.security import verify_token
from app.api.dispatcher.auth import router as dispatcher_auth_router

router = APIRouter(prefix="/disp", tags=["dispatch"])
templates = Jinja2Templates(directory="templates")

router.include_router(dispatcher_auth_router)

@router.get("/", response_class=HTMLResponse)
async def dispatch_dashboard(request: Request, db: Session = Depends(get_db)):
    dispatcher = getattr(request.state, 'dispatcher', None)
    taxipark_id = getattr(request.state, 'taxipark_id', None)
    
    if not dispatcher:
        return RedirectResponse(url='/disp/auth/login', status_code=302)
    
    from app.services.dispatcher_service import DispatcherService
    stats = DispatcherService.get_dispatcher_stats(db, taxipark_id)
    
    return templates.TemplateResponse("dispatcher/index.html", {
        "request": request,
        "dispatcher": dispatcher,
        "taxipark_id": taxipark_id,
        "balance": stats["balance"],
        "drivers_count": stats["drivers_count"],
        "orders_stats": stats["orders_stats"],
        "orders": stats["orders"]
    })

@router.get("/analytics", response_class=HTMLResponse)
async def dispatch_analytics(request: Request):
    return HTMLResponse(content="<h1>Аналитика диспетчерской</h1><p>Страница в разработке</p>")

@router.get("/drivers", response_class=HTMLResponse)
async def dispatch_drivers(request: Request, db: Session = Depends(get_db), page: int = 1, per_page: int = 10):
    dispatcher = getattr(request.state, 'dispatcher', None)
    taxipark_id = getattr(request.state, 'taxipark_id', None)
    
    if not dispatcher:
        return RedirectResponse(url='/disp/auth/login', status_code=302)
    
    from app.models.driver import Driver
    from app.services.dispatcher_service import DispatcherService
    from sqlalchemy import func
    
    # Получаем общее количество водителей
    total_drivers = db.query(Driver).filter(Driver.taxipark_id == taxipark_id).count()
    
    # Вычисляем пагинацию
    total_pages = (total_drivers + per_page - 1) // per_page
    offset = (page - 1) * per_page
    
    # Получаем водителей для текущей страницы
    drivers = db.query(Driver).filter(Driver.taxipark_id == taxipark_id).offset(offset).limit(per_page).all()
    
    # Получаем статистику
    stats = DispatcherService.get_dispatcher_stats(db, taxipark_id)
    
    # Подсчитываем статистику водителей
    active_drivers = db.query(Driver).filter(Driver.taxipark_id == taxipark_id, Driver.is_active == True).count()
    
    return templates.TemplateResponse("dispatcher/drivers.html", {
        "request": request,
        "dispatcher": dispatcher,
        "taxipark_id": taxipark_id,
        "drivers": drivers,
        "total_drivers": total_drivers,
        "active_drivers": active_drivers,
        "balance": stats["balance"],
        "current_page": page,
        "total_pages": total_pages,
        "per_page": per_page
    })

@router.get("/cars", response_class=HTMLResponse)
async def dispatch_cars(request: Request, db: Session = Depends(get_db), page: int = 1, per_page: int = 10):
    dispatcher = getattr(request.state, 'dispatcher', None)
    taxipark_id = getattr(request.state, 'taxipark_id', None)
    
    if not dispatcher:
        return RedirectResponse(url='/disp/auth/login', status_code=302)
    
    from app.models.driver import Driver
    from app.services.dispatcher_service import DispatcherService
    from sqlalchemy import func
    
    # Получаем автомобили (через водителей) для данного таксопарка
    total_cars = db.query(Driver).filter(Driver.taxipark_id == taxipark_id).count()
    
    # Вычисляем пагинацию
    total_pages = (total_cars + per_page - 1) // per_page
    offset = (page - 1) * per_page
    
    # Получаем автомобили для текущей страницы
    cars = db.query(Driver).filter(Driver.taxipark_id == taxipark_id).offset(offset).limit(per_page).all()
    
    # Получаем статистику
    stats = DispatcherService.get_dispatcher_stats(db, taxipark_id)
    
    # Подсчитываем статистику автомобилей
    active_cars = db.query(Driver).filter(Driver.taxipark_id == taxipark_id, Driver.is_active == True).count()
    
    return templates.TemplateResponse("dispatcher/cars.html", {
        "request": request,
        "dispatcher": dispatcher,
        "taxipark_id": taxipark_id,
        "cars": cars,
        "total_cars": total_cars,
        "active_cars": active_cars,
        "balance": stats["balance"],
        "current_page": page,
        "total_pages": total_pages,
        "per_page": per_page
    })

@router.get("/new-order", response_class=HTMLResponse)
async def dispatch_new_order(request: Request, db: Session = Depends(get_db)):
    dispatcher = getattr(request.state, 'dispatcher', None)
    taxipark_id = getattr(request.state, 'taxipark_id', None)
    
    if not dispatcher:
        return RedirectResponse(url='/disp/auth/login', status_code=302)
    
    from app.models.driver import Driver
    from app.models.order import Order
    from app.services.dispatcher_service import DispatcherService
    from datetime import datetime
    import random
    import pytz
    
    # Получаем активных водителей
    drivers = db.query(Driver).filter(
        Driver.taxipark_id == taxipark_id,
        Driver.is_active == True
    ).all()
    
    # Получаем последние заказы
    recent_orders = db.query(Order).filter(
        Order.taxipark_id == taxipark_id
    ).order_by(Order.created_at.desc()).limit(10).all()
    
    # Получаем статистику
    stats = DispatcherService.get_dispatcher_stats(db, taxipark_id)
    
    # Генерируем номер заказа
    order_number = f"WDD10{random.randint(1000000, 9999999)}"
    
    # Получаем время Кыргызстана (UTC+6)
    kyrgyzstan_tz = pytz.timezone('Etc/GMT-6')  # UTC+6, фиксированный часовой пояс
    current_datetime = datetime.now(kyrgyzstan_tz)
    
    # Получаем информацию о таксопарке
    from app.models.taxipark import TaxiPark
    taxipark = db.query(TaxiPark).filter(TaxiPark.id == taxipark_id).first()
    
    return templates.TemplateResponse("dispatcher/new_order.html", {
        "request": request,
        "dispatcher": dispatcher,
        "taxipark_id": taxipark_id,
        "taxipark": taxipark,
        "drivers": drivers,
        "recent_orders": recent_orders,
        "balance": stats["balance"],
        "order_number": order_number,
        "current_datetime": current_datetime
    })

@router.get("/chat", response_class=HTMLResponse)
async def dispatch_chat(request: Request):
    return HTMLResponse(content="<h1>Чат с водителями</h1><p>Страница в разработке</p>")

@router.get("/balance-request", response_class=HTMLResponse)
async def dispatch_balance_request(request: Request):
    return HTMLResponse(content="<h1>Запрос на баланс</h1><p>Страница в разработке</p>")

@router.get("/balance-topup", response_class=HTMLResponse)
async def dispatch_balance_topup(request: Request, db: Session = Depends(get_db), page: int = 1, per_page: int = 10):
    dispatcher = getattr(request.state, 'dispatcher', None)
    taxipark_id = getattr(request.state, 'taxipark_id', None)
    
    if not dispatcher:
        return RedirectResponse(url='/disp/auth/login', status_code=302)
    
    from app.models.driver import Driver
    from app.services.dispatcher_service import DispatcherService
    
    # Получаем водителей для пополнения баланса
    total_drivers = db.query(Driver).filter(Driver.taxipark_id == taxipark_id).count()
    
    # Вычисляем пагинацию
    total_pages = (total_drivers + per_page - 1) // per_page
    offset = (page - 1) * per_page
    
    # Получаем водителей для текущей страницы
    drivers = db.query(Driver).filter(Driver.taxipark_id == taxipark_id).offset(offset).limit(per_page).all()
    
    # Получаем статистику
    stats = DispatcherService.get_dispatcher_stats(db, taxipark_id)
    
    # Получаем информацию о таксопарке
    from app.models.taxipark import TaxiPark
    taxipark = db.query(TaxiPark).filter(TaxiPark.id == taxipark_id).first()
    
    return templates.TemplateResponse("dispatcher/pay_balance.html", {
        "request": request,
        "dispatcher": dispatcher,
        "taxipark_id": taxipark_id,
        "taxipark": taxipark,
        "drivers": drivers,
        "total_drivers": total_drivers,
        "balance": stats["balance"],
        "current_page": page,
        "total_pages": total_pages,
        "per_page": per_page
    })

@router.get("/driver-create", response_class=HTMLResponse)
async def dispatch_driver_create(request: Request):
    return HTMLResponse(content="<h1>Создание водителя</h1><p>Страница в разработке</p>")

@router.get("/photo-control", response_class=HTMLResponse)
async def dispatch_photo_control(request: Request, db: Session = Depends(get_db), status: str = "all"):
    dispatcher = getattr(request.state, 'dispatcher', None)
    taxipark_id = getattr(request.state, 'taxipark_id', None)
    
    if not dispatcher:
        return RedirectResponse(url='/disp/auth/login', status_code=302)
    
    from app.models.driver import Driver
    from app.services.dispatcher_service import DispatcherService
    
    # Получаем водителей для фото контроля
    query = db.query(Driver).filter(Driver.taxipark_id == taxipark_id)
    
    # Фильтрация по статусу
    if status == "approved":
        # Принятые - активные водители
        query = query.filter(Driver.is_active == True)
    elif status == "rejected":
        # Отклоненные - неактивные водители
        query = query.filter(Driver.is_active == False)
    elif status == "pending":
        # В ожидании - можно использовать дату создания для новых водителей
        from datetime import datetime, timedelta
        recent_date = datetime.now() - timedelta(days=7)  # Водители за последние 7 дней
        query = query.filter(Driver.created_at >= recent_date)
    
    drivers = query.all()
    
    # Получаем статистику
    stats = DispatcherService.get_dispatcher_stats(db, taxipark_id)
    
    # Подсчитываем статистику по статусам
    total_drivers = db.query(Driver).filter(Driver.taxipark_id == taxipark_id).count()
    active_drivers = db.query(Driver).filter(Driver.taxipark_id == taxipark_id, Driver.is_active == True).count()
    inactive_drivers = db.query(Driver).filter(Driver.taxipark_id == taxipark_id, Driver.is_active == False).count()
    
    return templates.TemplateResponse("dispatcher/drivers_control.html", {
        "request": request,
        "dispatcher": dispatcher,
        "taxipark_id": taxipark_id,
        "drivers": drivers,
        "total_drivers": total_drivers,
        "active_drivers": active_drivers,
        "inactive_drivers": inactive_drivers,
        "balance": stats["balance"],
        "current_status": status
    })

@router.get("/profile", response_class=HTMLResponse)
async def dispatch_profile(request: Request, db: Session = Depends(get_db)):
    dispatcher = getattr(request.state, 'dispatcher', None)
    taxipark_id = getattr(request.state, 'taxipark_id', None)
    
    if not dispatcher:
        return RedirectResponse(url='/disp/auth/login', status_code=302)
    
    from app.services.dispatcher_service import DispatcherService
    from app.models.taxipark import TaxiPark
    from datetime import datetime, timedelta
    
    # Получаем информацию о таксопарке
    taxipark = db.query(TaxiPark).filter(TaxiPark.id == taxipark_id).first()
    
    # Вычисляем количество дней работы
    days_working = 0
    if dispatcher.created_at:
        days_working = (datetime.now() - dispatcher.created_at).days
    
    return templates.TemplateResponse("dispatcher/profile.html", {
        "request": request,
        "dispatcher": dispatcher,
        "taxipark": taxipark,
        "days_working": days_working
    })

@router.get("/api/dashboard-stats")
async def get_dashboard_stats(request: Request, db: Session = Depends(get_db)):
    taxipark_id = getattr(request.state, 'taxipark_id', None)
    
    if not taxipark_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Таксопарк не определен"
        )
    
    from app.services.dispatcher_service import DispatcherService
    stats = DispatcherService.get_dispatcher_stats(db, taxipark_id)
    
    return {
        "balance": stats["balance"],
        "drivers_count": stats["drivers_count"],
        "orders_stats": stats["orders_stats"],
        "orders": [
            {
                "id": order.id,
                "order_number": order.id,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "status": order.status,
                "phone": order.client_phone,
                "from_address": order.pickup_address,
                "to_address": order.destination_address,
                "driver_name": "Позывной",
                "amount": order.price,
                "tariff": "Комфорт"
            }
            for order in stats["orders"]
        ]
    }

@router.post("/api/driver-status")
async def update_driver_status(request: Request, db: Session = Depends(get_db)):
    dispatcher = getattr(request.state, 'dispatcher', None)
    taxipark_id = getattr(request.state, 'taxipark_id', None)
    
    if not dispatcher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        data = await request.json()
        driver_id = data.get('driver_id')
        is_active = data.get('is_active')
        
        if not driver_id or is_active is None:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        from app.models.driver import Driver
        
        # Проверяем, что водитель принадлежит к тому же таксопарку
        driver = db.query(Driver).filter(
            Driver.id == driver_id,
            Driver.taxipark_id == taxipark_id
        ).first()
        
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        # Обновляем статус
        driver.is_active = is_active
        db.commit()
        
        return {"success": True, "message": "Driver status updated successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/topup-balance")
async def topup_driver_balance(request: Request, db: Session = Depends(get_db)):
    dispatcher = getattr(request.state, 'dispatcher', None)
    taxipark_id = getattr(request.state, 'taxipark_id', None)
    
    if not dispatcher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        data = await request.json()
        driver_id = data.get('driver_id')
        amount = data.get('amount')
        
        if not driver_id or not amount:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        
        from app.models.driver import Driver
        
        driver = db.query(Driver).filter(
            Driver.id == driver_id,
            Driver.taxipark_id == taxipark_id
        ).first()
        
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        current_balance = driver.balance if driver.balance else 0
        driver.balance = current_balance + amount
        db.commit()
        
        return {
            "success": True, 
            "message": "Balance topped up successfully",
            "new_balance": driver.balance
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/create-order")
async def create_order(request: Request, db: Session = Depends(get_db)):
    dispatcher = getattr(request.state, 'dispatcher', None)
    taxipark_id = getattr(request.state, 'taxipark_id', None)
    
    if not dispatcher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        data = await request.json()
        
        required_fields = ['driver_id', 'tariff', 'payment_method', 'pickup_address', 'destination_address']
        for field in required_fields:
            if not data.get(field):
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        from app.models.driver import Driver
        from app.models.order import Order
        from datetime import datetime
        
        driver = db.query(Driver).filter(
            Driver.id == data['driver_id'],
            Driver.taxipark_id == taxipark_id,
            Driver.is_active == True
        ).first()
        
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found or inactive")
        
        new_order = Order(
            order_number=data.get('order_number', ''),
            driver_id=data['driver_id'],
            taxipark_id=taxipark_id,
            pickup_address=data['pickup_address'],
            destination_address=data['destination_address'],
            status='pending',
            payment_method=data['payment_method'],
            tariff=data['tariff'],
            price=0.0, 
            notes=data.get('notes', ''),
            client_phone='', 
            created_at=datetime.now()
        )
        
        db.add(new_order)
        db.commit()
        
        return {
            "success": True,
            "message": "Order created successfully",
            "order_id": new_order.id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
