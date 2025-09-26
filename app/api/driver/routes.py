from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.session import get_db
from app.models.order import Order
from app.models.driver import Driver
from datetime import datetime
from app.websocket.manager import websocket_manager
from .order_routes import router as order_router

router = APIRouter(prefix="/driver", tags=["driver"])

# Включаем маршруты для работы с заказами
router.include_router(order_router)

class FCMTokenUpdate(BaseModel):
    phone_number: str
    fcm_token: str

@router.put("/api/orders/{order_id}/status")
async def update_order_status_by_driver(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Обновить статус заказа водителем"""
    try:
        data = await request.json()
        status = data.get('status')
        driver_id = data.get('driver_id')
        
        if not status or not driver_id:
            raise HTTPException(status_code=400, detail="Status and driver_id are required")
        
        valid_statuses = ['accepted', 'navigating_to_a', 'arrived_at_a', 'navigating_to_b', 'completed', 'cancelled']
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
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
        await websocket_manager.send_to_taxipark(
            order.taxipark_id,
            {
                "type": "order_status_update",
                "order_id": order.id,
                "old_status": old_status,
                "new_status": status,
                "driver_id": driver_id,
                "timestamp": now.isoformat()
            }
        )
        
        return {
            "success": True,
            "message": "Order status updated successfully",
            "order": {
                "id": order.id,
                "status": order.status,
                "updated_at": now.isoformat()
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/orders/{order_id}")
async def get_order_by_driver(order_id: int, driver_id: int, db: Session = Depends(get_db)):
    """Получить заказ водителем"""
    try:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.driver_id == driver_id
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {
            "success": True,
            "order": order.to_dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/online-status")
async def update_online_status(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        driver_id = data.get('driver_id')
        status = data.get('status')
        
        if not driver_id or not status:
            raise HTTPException(status_code=400, detail="driver_id and status are required")
        
        if status not in ['online', 'offline']:
            raise HTTPException(status_code=400, detail="status must be 'online' or 'offline'")
        
        from app.models.driver import Driver
        from datetime import datetime
        
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        driver.online_status = status
        if status == 'online':
            driver.last_online_at = datetime.now()
        
        db.commit()
        
        from app.websocket.manager import websocket_manager
        await websocket_manager.send_to_taxipark({
            "type": "driver_status_changed",
            "driver_id": driver_id,
            "driver_name": f"{driver.first_name} {driver.last_name}",
            "status": status,
            "timestamp": datetime.now().isoformat()
        }, driver.taxipark_id)
        
        return {
            "success": True,
            "message": f"Driver status updated to {status}",
            "driver": driver.to_dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/online-drivers")
async def get_online_drivers(taxipark_id: int, db: Session = Depends(get_db)):
    try:
        from app.models.driver import Driver
        from datetime import datetime, timedelta
        
        # Автоматически отключаем водителей которые не активны более 2 минут
        cutoff_time = datetime.now() - timedelta(minutes=2)
        inactive_drivers = db.query(Driver).filter(
            Driver.taxipark_id == taxipark_id,
            Driver.online_status == 'online',
            Driver.last_online_at < cutoff_time
        ).all()
        
        for driver in inactive_drivers:
            driver.online_status = 'offline'
            print(f"🚫 Автоматически отключен водитель {driver.id} - нет активности")
        
        if inactive_drivers:
            db.commit()
        
        # Получаем только активных онлайн водителей
        online_drivers = db.query(Driver).filter(
            Driver.taxipark_id == taxipark_id,
            Driver.is_active == True,
            Driver.online_status == 'online'
        ).all()
        
        return {
            "success": True,
            "drivers": [driver.to_dict() for driver in online_drivers]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-fcm-token")
async def update_fcm_token(token_data: FCMTokenUpdate, db: Session = Depends(get_db)):
    """Обновить FCM токен водителя"""
    try:
        print(f"🔍 [API] Получен запрос на обновление FCM токена")
        print(f"🔍 [API] Номер телефона: {token_data.phone_number}")
        print(f"🔍 [API] FCM токен: {token_data.fcm_token[:20] if token_data.fcm_token else 'None'}...")
        
        driver = db.query(Driver).filter(Driver.phone_number == token_data.phone_number).first()
        
        if not driver:
            print(f"❌ [API] Водитель не найден для номера: {token_data.phone_number}")
            raise HTTPException(status_code=404, detail="Driver not found")
        
        print(f"🔍 [API] Найден водитель: {driver.first_name} {driver.last_name} (ID: {driver.id})")
        print(f"🔍 [API] Старый FCM токен: {driver.fcm_token[:20] if driver.fcm_token else 'None'}...")
        
        driver.fcm_token = token_data.fcm_token
        db.commit()
        
        print(f"✅ [API] FCM токен обновлен для водителя {driver.first_name} {driver.last_name}")
        print(f"✅ [API] Новый FCM токен: {driver.fcm_token[:20]}...")
        
        return {
            "success": True,
            "message": "FCM token updated successfully",
            "driver_id": driver.id
        }
        
    except Exception as e:
        print(f"❌ [API] Ошибка обновления FCM токена: {e}")
        print(f"❌ [API] Тип ошибки: {type(e).__name__}")
        import traceback
        print(f"❌ [API] Stack trace: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
