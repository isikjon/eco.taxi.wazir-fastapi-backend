from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.order import Order
from app.models.driver import Driver
from datetime import datetime
from app.websocket.manager import websocket_manager

router = APIRouter(prefix="/driver", tags=["driver"])

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
