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
async def dispatch_dashboard(
    request: Request, 
    db: Session = Depends(get_db),
    page: int = 1,
    per_page: int = 20,
    status: str = None
):
    dispatcher = getattr(request.state, 'dispatcher', None)
    taxipark_id = getattr(request.state, 'taxipark_id', None)
    
    if not dispatcher:
        return RedirectResponse(url='/disp/auth/login', status_code=302)
    
    from app.services.dispatcher_service import DispatcherService
    from app.models.order import Order
    from sqlalchemy.orm import joinedload
    from sqlalchemy import func
    
    # Получаем статистику
    stats = DispatcherService.get_dispatcher_stats(db, taxipark_id)
    
    # Базовый запрос с загрузкой водителей
    query = db.query(Order).options(joinedload(Order.driver)).filter(Order.taxipark_id == taxipark_id)
    
    # Применяем фильтр по статусу если указан
    if status and status != 'all':
        query = query.filter(Order.status == status)
    
    # Подсчитываем общее количество записей
    total_orders = query.count()
    
    # Вычисляем пагинацию
    total_pages = (total_orders + per_page - 1) // per_page if total_orders > 0 else 1
    offset = (page - 1) * per_page
    
    # Получаем заказы для текущей страницы
    orders = query.order_by(Order.created_at.desc()).offset(offset).limit(per_page).all()
    
    # Получаем уникальные статусы для статистики
    statuses = db.query(Order.status, func.count(Order.id)).filter(
        Order.taxipark_id == taxipark_id
    ).group_by(Order.status).all()
    
    return templates.TemplateResponse("dispatcher/index.html", {
        "request": request,
        "dispatcher": dispatcher,
        "taxipark_id": taxipark_id,
        "balance": stats["balance"],
        "drivers_count": stats["drivers_count"],
        "orders_stats": stats["orders_stats"],
        "orders": orders,
        "current_page": page,
        "total_pages": total_pages,
        "total_orders": total_orders,
        "per_page": per_page,
        "current_status": status,
        "statuses": statuses
    })

@router.get("/analytics", response_class=HTMLResponse)
async def dispatch_analytics(request: Request, db: Session = Depends(get_db)):
    dispatcher = getattr(request.state, 'dispatcher', None)
    taxipark_id = getattr(request.state, 'taxipark_id', None)
    
    if not dispatcher:
        return RedirectResponse(url='/disp/auth/login', status_code=302)
    
    from app.services.dispatcher_service import DispatcherService
    from app.models.order import Order
    from app.models.driver import Driver
    from app.models.transaction import DriverTransaction
    from sqlalchemy import func
    
    # Получаем статистику
    stats = DispatcherService.get_dispatcher_stats(db, taxipark_id)
    
    # Подсчитываем заказы по статусам
    orders_by_status = db.query(Order.status, func.count(Order.id)).filter(
        Order.taxipark_id == taxipark_id
    ).group_by(Order.status).all()
    orders_by_status_dict = dict(orders_by_status)
    
    # Подсчитываем заказы по тарифам
    tariffs_data = db.query(Order.tariff, func.count(Order.id)).filter(
        Order.taxipark_id == taxipark_id,
        Order.tariff.isnot(None)
    ).group_by(Order.tariff).all()
    tariffs_dict = dict(tariffs_data)
    
    # Подсчитываем активных водителей
    active_drivers = db.query(Driver).filter(
        Driver.taxipark_id == taxipark_id,
        Driver.is_active == True
    ).count()
    
    # Подсчитываем пополнения баланса
    total_topups = db.query(DriverTransaction).join(Driver).filter(
        Driver.taxipark_id == taxipark_id,
        DriverTransaction.type == 'topup'
    ).count()
    
    return templates.TemplateResponse("dispatcher/analytics.html", {
        "request": request,
        "dispatcher": dispatcher,
        "taxipark_id": taxipark_id,
        "balance": stats["balance"],
        "drivers_count": stats["drivers_count"],
        "total_orders": sum(orders_by_status_dict.values()) if orders_by_status_dict else 0,
        "orders_by_status": orders_by_status_dict,
        "tariffs_data": tariffs_dict,
        "active_drivers": active_drivers,
        "total_topups": total_topups
    })

@router.get("/drivers", response_class=HTMLResponse)
async def dispatch_drivers(
    request: Request, 
    db: Session = Depends(get_db), 
    page: int = 1, 
    per_page: int = 10,
    status: str = "all",
    tariff: str = ""
):
    try:
        dispatcher = getattr(request.state, 'dispatcher', None)
        taxipark_id = getattr(request.state, 'taxipark_id', None)
        
        if not dispatcher:
            return RedirectResponse(url='/disp/auth/login', status_code=302)
        
        from app.models.driver import Driver
        from app.services.dispatcher_service import DispatcherService
        from sqlalchemy import func
        
        # Базовый запрос для данного таксопарка
        query = db.query(Driver).filter(Driver.taxipark_id == taxipark_id)
        
        # Применяем фильтры
        if status == "active":
            query = query.filter(Driver.is_active == True)
        elif status == "inactive":
            query = query.filter(Driver.is_active == False)
        
        if tariff:
            query = query.filter(Driver.tariff == tariff)
        
        # Получаем общее количество водителей после фильтрации
        total_drivers = query.count()
        
        # Вычисляем пагинацию
        total_pages = (total_drivers + per_page - 1) // per_page
        offset = (page - 1) * per_page
        
        # Получаем водителей для текущей страницы
        drivers = query.offset(offset).limit(per_page).all()
        
        # Получаем статистику
        stats = DispatcherService.get_dispatcher_stats(db, taxipark_id)
        
        # Подсчитываем статистику водителей
        active_drivers = db.query(Driver).filter(Driver.taxipark_id == taxipark_id, Driver.is_active == True).count()
        
        # Получаем уникальные тарифы для фильтра
        all_drivers = db.query(Driver).filter(Driver.taxipark_id == taxipark_id).all()
        tariffs = set()
        for driver in all_drivers:
            if driver.tariff:
                tariffs.add(driver.tariff)
        
        # Проверяем, есть ли активные фильтры
        has_filters = any([status != "all", tariff])
        
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
            "per_page": per_page,
            "filters": {
                "status": status,
                "tariff": tariff
            },
            "filter_options": {
                "tariffs": sorted(tariffs)
            },
            "has_filters": has_filters
        })
    except Exception as e:
        print(f"Error in dispatch_drivers: {e}")
        return HTMLResponse(content=f"<h1>Ошибка</h1><p>Произошла ошибка при загрузке водителей: {str(e)}</p>", status_code=500)

@router.get("/cars", response_class=HTMLResponse)
async def dispatch_cars(
    request: Request, 
    db: Session = Depends(get_db), 
    page: int = 1, 
    per_page: int = 10,
    status: str = "all",
    brand: str = "",
    model: str = "",
    color: str = "",
    year: str = ""
):
    try:
        dispatcher = getattr(request.state, 'dispatcher', None)
        taxipark_id = getattr(request.state, 'taxipark_id', None)
        
        if not dispatcher:
            return RedirectResponse(url='/disp/auth/login', status_code=302)
        
        from app.models.driver import Driver
        from app.services.dispatcher_service import DispatcherService
        from sqlalchemy import func, or_
        
        # Базовый запрос для данного таксопарка
        query = db.query(Driver).filter(Driver.taxipark_id == taxipark_id)
        
        # Применяем фильтры
        if status == "active":
            query = query.filter(Driver.is_active == True)
        elif status == "inactive":
            query = query.filter(Driver.is_active == False)
        
        if brand:
            query = query.filter(Driver.car_model.contains(brand))
        
        if model:
            query = query.filter(Driver.car_model.contains(model))
        
        if color:
            query = query.filter(Driver.car_color.contains(color))
        
        if year:
            query = query.filter(Driver.car_year.contains(year))
        
        # Получаем общее количество после фильтрации
        total_cars = query.count()
        
        # Вычисляем пагинацию
        total_pages = (total_cars + per_page - 1) // per_page
        offset = (page - 1) * per_page
        
        # Получаем автомобили для текущей страницы
        cars = query.offset(offset).limit(per_page).all()
        
        # Получаем статистику
        stats = DispatcherService.get_dispatcher_stats(db, taxipark_id)
        
        # Подсчитываем статистику автомобилей
        active_cars = db.query(Driver).filter(Driver.taxipark_id == taxipark_id, Driver.is_active == True).count()
        
        # Получаем уникальные значения для фильтров
        all_cars = db.query(Driver).filter(Driver.taxipark_id == taxipark_id).all()
        
        # Извлекаем уникальные марки и модели
        brands = set()
        models = set()
        colors = set()
        years = set()
        
        for car in all_cars:
            if car.car_model:
                parts = car.car_model.split(' ', 1)
                if len(parts) > 0:
                    brands.add(parts[0])
                if len(parts) > 1:
                    models.add(parts[1])
            if car.car_color:
                colors.add(car.car_color)
            if car.car_year:
                years.add(car.car_year)
        
        # Проверяем, есть ли активные фильтры
        has_filters = any([status != "all", brand, model, color, year])
        
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
            "per_page": per_page,
            "filters": {
                "status": status,
                "brand": brand,
                "model": model,
                "color": color,
                "year": year
            },
            "filter_options": {
                "brands": sorted(brands),
                "models": sorted(models),
                "colors": sorted(colors),
                "years": sorted(years)
            },
            "has_filters": has_filters
        })
    except Exception as e:
        print(f"Error in dispatch_cars: {e}")
        return HTMLResponse(content=f"<h1>Ошибка</h1><p>Произошла ошибка при загрузке автомобилей: {str(e)}</p>", status_code=500)

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
    
    # Получаем последние заказы с загруженными водителями
    from sqlalchemy.orm import joinedload
    recent_orders = db.query(Order).options(joinedload(Order.driver)).filter(
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
async def dispatch_balance_topup(
    request: Request, 
    db: Session = Depends(get_db), 
    page: int = 1, 
    per_page: int = 10,
    status: str = "all",
    tariff: str = ""
):
    try:
        dispatcher = getattr(request.state, 'dispatcher', None)
        taxipark_id = getattr(request.state, 'taxipark_id', None)
        
        if not dispatcher:
            return RedirectResponse(url='/disp/auth/login', status_code=302)
        
        from app.models.driver import Driver
        from app.services.dispatcher_service import DispatcherService
        
        # Базовый запрос для данного таксопарка
        query = db.query(Driver).filter(Driver.taxipark_id == taxipark_id)
        
        # Применяем фильтры
        if status == "active":
            query = query.filter(Driver.is_active == True)
        elif status == "inactive":
            query = query.filter(Driver.is_active == False)
        
        if tariff:
            query = query.filter(Driver.tariff == tariff)
        
        # Получаем общее количество водителей после фильтрации
        total_drivers = query.count()
        
        # Вычисляем пагинацию
        total_pages = (total_drivers + per_page - 1) // per_page
        offset = (page - 1) * per_page
        
        # Получаем водителей для текущей страницы
        drivers = query.offset(offset).limit(per_page).all()
        
        # Получаем статистику
        stats = DispatcherService.get_dispatcher_stats(db, taxipark_id)
        
        # Получаем информацию о таксопарке
        from app.models.taxipark import TaxiPark
        taxipark = db.query(TaxiPark).filter(TaxiPark.id == taxipark_id).first()
        
        # Получаем уникальные тарифы для фильтра
        all_drivers = db.query(Driver).filter(Driver.taxipark_id == taxipark_id).all()
        tariffs = set()
        for driver in all_drivers:
            if driver.tariff:
                tariffs.add(driver.tariff)
        
        # Проверяем, есть ли активные фильтры
        has_filters = any([status != "all", tariff])
        
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
            "per_page": per_page,
            "filters": {
                "status": status,
                "tariff": tariff
            },
            "filter_options": {
                "tariffs": sorted(tariffs)
            },
            "has_filters": has_filters
        })
    except Exception as e:
        print(f"Error in dispatch_balance_topup: {e}")
        return HTMLResponse(content=f"<h1>Ошибка</h1><p>Произошла ошибка при загрузке страницы пополнения баланса: {str(e)}</p>", status_code=500)

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
                "order_number": order.order_number if order.order_number else order.id,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "status": order.status,
                "status_display": order.get_status_display(),
                "phone": order.client_phone,
                "from_address": order.pickup_address,
                "to_address": order.destination_address,
                "driver_name": order.get_driver_display_name(),
                "driver_phone": order.driver.phone_number if order.driver else None,
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
        
        # Обязательные поля
        required_fields = ['driver_id', 'tariff', 'payment_method', 'pickup_address', 'destination_address']
        for field in required_fields:
            if not data.get(field):
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        from app.models.driver import Driver
        from app.models.order import Order
        from datetime import datetime
        import random
        
        # Проверяем водителя
        driver = db.query(Driver).filter(
            Driver.id == data['driver_id'],
            Driver.taxipark_id == taxipark_id,
            Driver.is_active == True
        ).first()
        
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found or inactive")
        
        # Генерируем уникальный номер заказа
        order_number = data.get('order_number')
        if not order_number:
            order_number = f"WDD{random.randint(1000000, 9999999)}"
        
        # Создаем заказ
        new_order = Order(
            order_number=order_number,
            client_name=data.get('client_name', ''),
            client_phone=data.get('client_phone', ''),
            pickup_address=data['pickup_address'],
            pickup_latitude=data.get('pickup_latitude'),
            pickup_longitude=data.get('pickup_longitude'),
            destination_address=data['destination_address'],
            destination_latitude=data.get('destination_latitude'),
            destination_longitude=data.get('destination_longitude'),
            price=data.get('price', 0.0),
            distance=data.get('distance'),
            duration=data.get('duration'),
            status='received',  # Новый статус
            driver_id=data['driver_id'],
            taxipark_id=taxipark_id,
            tariff=data['tariff'],
            payment_method=data['payment_method'],
            notes=data.get('notes', ''),
            created_at=datetime.now()
        )
        
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        
        # Отправляем заказ водителю через WebSocket
        from app.websocket.manager import websocket_manager
        await websocket_manager.broadcast_new_order(
            new_order.to_dict(), 
            taxipark_id, 
            new_order.driver_id
        )
        
        return {
            "success": True,
            "message": "Order created successfully",
            "order": new_order.to_dict()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/orders")
async def get_orders(request: Request, db: Session = Depends(get_db)):
    """Получить список заказов для диспетчера"""
    dispatcher = getattr(request.state, 'dispatcher', None)
    taxipark_id = getattr(request.state, 'taxipark_id', None)
    
    if not dispatcher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from app.models.order import Order
        from sqlalchemy import desc
        
        orders = db.query(Order).filter(
            Order.taxipark_id == taxipark_id
        ).order_by(desc(Order.created_at)).limit(50).all()
        
        return {
            "success": True,
            "orders": [order.to_dict() for order in orders]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/orders/{order_id}")
async def get_order(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Получить конкретный заказ"""
    dispatcher = getattr(request.state, 'dispatcher', None)
    taxipark_id = getattr(request.state, 'taxipark_id', None)
    
    if not dispatcher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from app.models.order import Order
        
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.taxipark_id == taxipark_id
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {
            "success": True,
            "order": order.to_dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/orders/{order_id}/status")
async def update_order_status(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Обновить статус заказа"""
    dispatcher = getattr(request.state, 'dispatcher', None)
    taxipark_id = getattr(request.state, 'taxipark_id', None)
    
    if not dispatcher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        data = await request.json()
        new_status = data.get('status')
        
        if not new_status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        valid_statuses = ['received', 'accepted', 'navigating_to_a', 'arrived_at_a', 'navigating_to_b', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        from app.models.order import Order
        from datetime import datetime
        
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.taxipark_id == taxipark_id
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Обновляем статус и соответствующие временные метки
        order.status = new_status
        now = datetime.now()
        
        if new_status == 'accepted':
            order.accepted_at = now
        elif new_status == 'arrived_at_a':
            order.arrived_at_a = now
        elif new_status == 'navigating_to_b':
            order.started_to_b = now
        elif new_status == 'completed':
            order.completed_at = now
        elif new_status == 'cancelled':
            order.cancelled_at = now
        
        db.commit()
        
        # Отправляем обновление статуса через WebSocket
        from app.websocket.manager import websocket_manager
        await websocket_manager.broadcast_order_status_update(
            order.to_dict(), 
            taxipark_id
        )
        
        return {
            "success": True,
            "message": "Order status updated successfully",
            "order": order.to_dict()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
