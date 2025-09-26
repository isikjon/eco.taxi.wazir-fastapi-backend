from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.driver import Driver
from app.models.order import Order
from datetime import datetime

router = APIRouter(prefix="/driver", tags=["driver_orders"])

@router.put("/orders/{order_id}/accept")
async def accept_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Принять заказ водителем"""
    try:
        data = await request.json()
        driver_id = data.get('driver_id')
        
        if not driver_id:
            raise HTTPException(status_code=400, detail="Driver ID is required")
        
        # Проверяем водителя
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        # Проверяем заказ
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.driver_id == driver_id,
            Order.status == 'received'
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found or already processed")
        
        # Обновляем статус заказа
        order.status = 'accepted'
        order.accepted_at = datetime.now()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Order accepted successfully",
            "order": order.to_dict()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/orders/{order_id}/reject")
async def reject_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Отклонить заказ водителем"""
    try:
        data = await request.json()
        driver_id = data.get('driver_id')
        
        if not driver_id:
            raise HTTPException(status_code=400, detail="Driver ID is required")
        
        # Проверяем водителя
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        # Проверяем заказ
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.driver_id == driver_id,
            Order.status == 'received'
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found or already processed")
        
        # Обновляем статус заказа
        order.status = 'cancelled'
        order.cancelled_at = datetime.now()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Order rejected successfully",
            "order": order.to_dict()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Обновить статус заказа водителем"""
    try:
        data = await request.json()
        driver_id = data.get('driver_id')
        new_status = data.get('status')
        
        if not driver_id or not new_status:
            raise HTTPException(status_code=400, detail="Driver ID and status are required")
        
        # Проверяем водителя
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        # Проверяем заказ
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.driver_id == driver_id
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Валидируем статус
        valid_statuses = ['accepted', 'navigating_to_a', 'arrived_at_a', 'navigating_to_b', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        # Обновляем статус и соответствующие временные метки
        order.status = new_status
        now = datetime.now()
        
        if new_status == 'navigating_to_a':
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
            order.taxipark_id
        )
        
        return {
            "success": True,
            "message": "Order status updated successfully",
            "order": order.to_dict()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
