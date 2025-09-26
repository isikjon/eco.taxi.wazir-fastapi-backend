from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.websocket.manager import websocket_manager
from app.core.security import verify_token
import json

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/orders")
async def websocket_orders_endpoint(websocket: WebSocket, token: str = None):
    """WebSocket endpoint для заказов"""
    try:
        # Проверяем токен если передан
        if token:
            try:
                payload = verify_token(token)
                user_id = payload.get("sub")
                user_type = payload.get("type", "driver")
                taxipark_id = payload.get("taxipark_id")
            except Exception as e:
                await websocket.close(code=1008, reason="Invalid token")
                return
        else:
            # Для тестирования без токена
            user_id = "test_user"
            user_type = "driver"
            taxipark_id = 1
        
        # Подключаем к WebSocket
        await websocket_manager.connect(websocket, user_id, user_type, taxipark_id)
        
        # Слушаем сообщения
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Обрабатываем входящие сообщения
                await handle_websocket_message(message, user_id, user_type, taxipark_id)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                print(f"Ошибка обработки WebSocket сообщения: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Internal server error"
                }))
    
    except WebSocketDisconnect:
        pass
    finally:
        websocket_manager.disconnect(user_id)

async def handle_websocket_message(message: dict, user_id: str, user_type: str, taxipark_id: int):
    """Обработка входящих WebSocket сообщений"""
    message_type = message.get("type")
    
    if message_type == "ping":
        # Ответ на ping
        await websocket_manager.send_personal_message({
            "type": "pong",
            "timestamp": message.get("timestamp")
        }, user_id)
    
    elif message_type == "order_status_update":
        # Обновление статуса заказа от водителя
        order_id = message.get("order_id")
        status = message.get("status")
        timestamp = message.get("timestamp")
        
        if order_id and status:
            try:
                # Обновляем статус в базе данных
                from app.models.order import Order
                from datetime import datetime
                
                # Получаем сессию БД
                from app.database.session import SessionLocal
                db = SessionLocal()
                
                try:
                    # Находим заказ
                    order = db.query(Order).filter(Order.id == order_id).first()
                    
                    if order:
                        # Обновляем статус
                        old_status = order.status
                        order.status = status
                        
                        # Обновляем временные метки в зависимости от статуса
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
                        
                        # Отправляем обновление диспетчерам
                        await websocket_manager.send_to_taxipark({
                            "type": "order_status_changed",
                            "order_id": order_id,
                            "order_number": order.order_number,
                            "old_status": old_status,
                            "new_status": status,
                            "driver_id": user_id,
                            "timestamp": timestamp or now.isoformat()
                        }, taxipark_id, exclude_user=user_id)
                        
                        await websocket_manager.send_personal_message({
                            "type": "status_update_confirmed",
                            "order_id": order_id,
                            "status": status,
                            "message": "Статус заказа обновлен"
                        }, user_id)
                        
                        print(f"✅ Статус заказа {order_id} обновлен: {old_status} → {status}")
                    else:
                        await websocket_manager.send_personal_message({
                            "type": "error",
                            "message": f"Заказ {order_id} не найден"
                        }, user_id)
                        
                finally:
                    db.close()
                    
            except Exception as e:
                print(f"❌ Ошибка обновления статуса заказа: {e}")
                await websocket_manager.send_personal_message({
                    "type": "error",
                    "message": f"Ошибка обновления статуса: {str(e)}"
                }, user_id)
    
    elif message_type == "driver_location_update":
        # Обновление местоположения водителя
        latitude = message.get("latitude")
        longitude = message.get("longitude")
        
        if latitude and longitude:
            # TODO: Сохранить местоположение водителя
            # TODO: Отправить обновление диспетчерам
            
            await websocket_manager.send_personal_message({
                "type": "location_update_confirmed",
                "message": "Местоположение обновлено"
            }, user_id)
    
    elif message_type == "driver_status_update":
        # Обновление статуса водителя
        driver_id = message.get("driver_id")
        status = message.get("status")
        timestamp = message.get("timestamp")
        
        if driver_id and status:
            try:
                from app.models.driver import Driver
                from datetime import datetime
                
                from app.database.session import SessionLocal
                db = SessionLocal()
                
                try:
                    driver = db.query(Driver).filter(Driver.id == driver_id).first()
                    
                    if driver:
                        old_status = driver.online_status
                        driver.online_status = status
                        if status == 'online':
                            driver.last_online_at = datetime.now()
                        
                        db.commit()
                        
                        await websocket_manager.send_to_taxipark({
                            "type": "driver_status_changed",
                            "driver_id": driver_id,
                            "driver_name": f"{driver.first_name} {driver.last_name}",
                            "old_status": old_status,
                            "new_status": status,
                            "timestamp": timestamp or datetime.now().isoformat()
                        }, taxipark_id, exclude_user=user_id)
                        
                        await websocket_manager.send_personal_message({
                            "type": "status_update_confirmed",
                            "driver_id": driver_id,
                            "status": status,
                            "message": "Статус водителя обновлен"
                        }, user_id)
                        
                        print(f"✅ Статус водителя {driver_id} обновлен: {old_status} → {status}")
                    else:
                        await websocket_manager.send_personal_message({
                            "type": "error",
                            "message": f"Водитель {driver_id} не найден"
                        }, user_id)
                        
                finally:
                    db.close()
                    
            except Exception as e:
                print(f"❌ Ошибка обновления статуса водителя: {e}")
                await websocket_manager.send_personal_message({
                    "type": "error",
                    "message": f"Ошибка обновления статуса: {str(e)}"
                }, user_id)
    
    else:
        # Неизвестный тип сообщения
        await websocket_manager.send_personal_message({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }, user_id)

@router.websocket("/ws/orders/dispatcher")
async def websocket_dispatcher_endpoint(websocket: WebSocket, token: str = None):
    """WebSocket endpoint для диспетчеров"""
    try:
        # Проверяем токен если передан
        if token:
            try:
                payload = verify_token(token)
                dispatcher_id = payload.get("sub")
                taxipark_id = payload.get("taxipark_id")
            except Exception as e:
                await websocket.close(code=1008, reason="Invalid token")
                return
        else:
            # Для тестирования без токена
            dispatcher_id = "test_dispatcher"
            taxipark_id = 1
        
        # Подключаем к WebSocket
        await websocket_manager.connect(websocket, f"dispatcher_{dispatcher_id}", "dispatcher", taxipark_id)
        
        # Слушаем сообщения
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Обрабатываем входящие сообщения от диспетчера
                await handle_dispatcher_message(message, dispatcher_id, taxipark_id)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                print(f"Ошибка обработки WebSocket сообщения диспетчера: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Internal server error"
                }))
    
    except WebSocketDisconnect:
        pass
    finally:
        websocket_manager.disconnect(f"dispatcher_{dispatcher_id}")

async def handle_dispatcher_message(message: dict, dispatcher_id: str, taxipark_id: int):
    """Обработка сообщений от диспетчера"""
    message_type = message.get("type")
    
    if message_type == "ping":
        # Ответ на ping
        await websocket_manager.send_personal_message({
            "type": "pong",
            "timestamp": message.get("timestamp")
        }, f"dispatcher_{dispatcher_id}")
    
    elif message_type == "broadcast_message":
        # Широковещательное сообщение всем водителям таксопарка
        broadcast_message = message.get("message", "")
        
        await websocket_manager.send_to_taxipark({
            "type": "dispatcher_broadcast",
            "message": broadcast_message,
            "from": f"Диспетчер {dispatcher_id}"
        }, taxipark_id, exclude_user=f"dispatcher_{dispatcher_id}")
        
        await websocket_manager.send_personal_message({
            "type": "broadcast_sent",
            "message": "Сообщение отправлено всем водителям"
        }, f"dispatcher_{dispatcher_id}")
    
    else:
        # Неизвестный тип сообщения
        await websocket_manager.send_personal_message({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }, f"dispatcher_{dispatcher_id}")

@router.get("/ws/status")
async def websocket_status():
    """Получить статус WebSocket соединений"""
    return {
        "active_connections": websocket_manager.get_connection_count(),
        "taxipark_connections": {
            str(taxipark_id): websocket_manager.get_taxipark_connections_count(taxipark_id)
            for taxipark_id in websocket_manager.taxipark_connections.keys()
        }
    }
