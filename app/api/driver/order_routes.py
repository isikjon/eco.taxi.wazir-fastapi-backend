from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.driver import Driver
from app.models.order import Order
from app.models.taxipark import TaxiPark
from app.models.transaction import DriverTransaction
from datetime import datetime
import uuid

router = APIRouter(tags=["driver_orders"])

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

@router.put("/api/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Обновить статус заказа водителем"""
    print(f"🔍 [OrderRoutes] Endpoint called: PUT /api/orders/{order_id}/status")
    try:
        data = await request.json()
        driver_id = int(data.get('driver_id'))  # Убеждаемся, что это integer
        new_status = data.get('status')
        
        print(f"🔍 [OrderRoutes] Received request for order {order_id}")
        print(f"🔍 [OrderRoutes] Driver ID: {driver_id}, Status: {new_status}")
        
        if not driver_id or not new_status:
            raise HTTPException(status_code=400, detail="Driver ID and status are required")
        
        # Проверяем водителя
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            print(f"❌ [OrderRoutes] Driver {driver_id} not found")
            raise HTTPException(status_code=404, detail="Driver not found")
        
        print(f"✅ [OrderRoutes] Driver found: {driver.first_name} {driver.last_name}")
        
        # Проверяем заказ
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.driver_id == driver_id
        ).first()
        
        if not order:
            # Давайте проверим, существует ли заказ вообще
            order_exists = db.query(Order).filter(Order.id == order_id).first()
            if order_exists:
                print(f"❌ [OrderRoutes] Order {order_id} exists but driver_id is {order_exists.driver_id}, not {driver_id}")
                raise HTTPException(status_code=404, detail=f"Order {order_id} is not assigned to driver {driver_id}")
            else:
                print(f"❌ [OrderRoutes] Order {order_id} does not exist")
                raise HTTPException(status_code=404, detail="Order not found")
        
        print(f"✅ [OrderRoutes] Order found: {order.order_number}, current status: {order.status}")
        
        # Валидируем статус
        valid_statuses = ['accepted', 'navigating_to_a', 'arrived_at_a', 'navigating_to_b', 'completed', 'cancelled', 'rejected_by_driver']
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        # Логика списания комиссии при принятии заказа
        if new_status == 'accepted' and order.status == 'received':
            commission_result = await _process_order_commission(db, driver, order)
            if not commission_result['success']:
                return {
                    "success": False,
                    "error": commission_result['error'],
                    "error_code": "INSUFFICIENT_BALANCE",
                    "required_amount": commission_result.get('required_amount'),
                    "current_balance": commission_result.get('current_balance')
                }
        
        # Обновляем статус и соответствующие временные метки
        order.status = new_status
        now = datetime.now()
        
        if new_status == 'accepted':
            order.accepted_at = now
        elif new_status == 'navigating_to_a':
            order.accepted_at = now
        elif new_status == 'arrived_at_a':
            order.arrived_at_a = now
        elif new_status == 'navigating_to_b':
            order.started_to_b = now
        elif new_status == 'completed':
            order.completed_at = now
        elif new_status == 'cancelled':
            order.cancelled_at = now
        elif new_status == 'rejected_by_driver':
            order.cancelled_at = now
        
        db.commit()
        
        # Отправляем обновление статуса через WebSocket
        from app.websocket.manager import websocket_manager
        
        if new_status == 'rejected_by_driver':
            await websocket_manager.send_personal_message(
                {
                    "type": "order_rejected",
                    "data": order.to_dict(),
                    "timestamp": now.isoformat()
                },
                f"client_{order.client_phone}"
            )
        elif new_status == 'accepted':
            await websocket_manager.send_personal_message(
                {
                    "type": "order_accepted",
                    "data": order.to_dict(),
                    "timestamp": now.isoformat()
                },
                f"client_{order.client_phone}"
            )
        elif new_status == 'arrived_at_a':
            await websocket_manager.send_personal_message(
                {
                    "type": "driver_arrived",
                    "data": order.to_dict(),
                    "timestamp": now.isoformat()
                },
                f"client_{order.client_phone}"
            )
        elif new_status == 'completed':
            await websocket_manager.send_personal_message(
                {
                    "type": "order_completed",
                    "data": order.to_dict(),
                    "timestamp": now.isoformat()
                },
                f"client_{order.client_phone}"
            )
        
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


async def _process_order_commission(db: Session, driver: Driver, order: Order) -> dict:
    """Обработать комиссию за принятие заказа"""
    try:
        print(f"💰 [Commission] Processing commission for order {order.id}")
        print(f"💰 [Commission] Driver: {driver.first_name} {driver.last_name} (ID: {driver.id})")
        print(f"💰 [Commission] Order price: {order.price}")
        
        # Получаем информацию о таксопарке
        taxipark = db.query(TaxiPark).filter(TaxiPark.id == driver.taxipark_id).first()
        if not taxipark:
            return {
                "success": False,
                "error": "Таксопарк не найден"
            }
        
        commission_percent = taxipark.commission_percent or 15.0  # По умолчанию 15%
        order_price = order.price or 0.0
        
        # Вычисляем комиссию
        commission_amount = (order_price * commission_percent) / 100
        
        print(f"💰 [Commission] Taxipark: {taxipark.name}")
        print(f"💰 [Commission] Commission percent: {commission_percent}%")
        print(f"💰 [Commission] Commission amount: {commission_amount}")
        
        # Проверяем баланс водителя
        current_balance = driver.balance or 0.0
        print(f"💰 [Commission] Current balance: {current_balance}")
        
        if current_balance < commission_amount:
            return {
                "success": False,
                "error": f"Недостаточно средств на балансе. Требуется: {commission_amount:.2f} сом, доступно: {current_balance:.2f} сом",
                "required_amount": commission_amount,
                "current_balance": current_balance,
                "commission_percent": commission_percent
            }
        
        # Списываем комиссию с баланса
        new_balance = current_balance - commission_amount
        driver.balance = new_balance
        
        # Создаем запись транзакции
        transaction = DriverTransaction(
            driver_id=driver.id,
            type='commission',
            amount=-commission_amount,  # Отрицательная сумма для списания
            description=f'Комиссия за принятие заказа #{order.order_number} ({commission_percent}% от {order_price} сом)',
            status='completed',
            reference=f'COMM_{order.id}_{uuid.uuid4().hex[:8].upper()}',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(transaction)
        
        print(f"💰 [Commission] Commission processed successfully:")
        print(f"💰 [Commission] - Commission amount: {commission_amount}")
        print(f"💰 [Commission] - Old balance: {current_balance}")
        print(f"💰 [Commission] - New balance: {new_balance}")
        print(f"💰 [Commission] - Transaction ID: {transaction.id}")
        
        return {
            "success": True,
            "commission_amount": commission_amount,
            "old_balance": current_balance,
            "new_balance": new_balance,
            "transaction_id": transaction.id
        }
        
    except Exception as e:
        print(f"❌ [Commission] Error processing commission: {e}")
        return {
            "success": False,
            "error": f"Ошибка обработки комиссии: {str(e)}"
        }
