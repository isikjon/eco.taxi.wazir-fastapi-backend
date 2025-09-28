from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio
from datetime import datetime

class WebSocketManager:
    def __init__(self):
        # Словарь для хранения активных соединений
        # Ключ: driver_id или dispatcher_id, Значение: WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Группы соединений по таксопаркам
        self.taxipark_connections: Dict[int, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, user_type: str, taxipark_id: int = None):
        """Подключить пользователя к WebSocket"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
        # Добавляем в группу таксопарка если указан
        if taxipark_id:
            if taxipark_id not in self.taxipark_connections:
                self.taxipark_connections[taxipark_id] = []
            if user_id not in self.taxipark_connections[taxipark_id]:
                self.taxipark_connections[taxipark_id].append(user_id)
        
        print(f"✅ WebSocket подключен: {user_type} {user_id} (таксопарк: {taxipark_id})")
        
        # Отправляем подтверждение подключения
        await self.send_personal_message({
            "type": "connection_established",
            "message": "WebSocket подключен успешно",
            "timestamp": datetime.now().isoformat()
        }, user_id)
    
    def disconnect(self, user_id: str):
        """Отключить пользователя от WebSocket"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Удаляем из групп таксопарков
        for taxipark_id, users in self.taxipark_connections.items():
            if user_id in users:
                users.remove(user_id)
        
        print(f"❌ WebSocket отключен: {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Отправить сообщение конкретному пользователю"""
        print(f"🔍 [WebSocket Manager] send_personal_message called with user_id: {user_id}")
        print(f"🔍 [WebSocket Manager] active_connections keys: {list(self.active_connections.keys())}")
        
        if user_id in self.active_connections:
            try:
                message_json = json.dumps(message)
                print(f"🔍 [WebSocket Manager] Sending message to {user_id}: {message_json}")
                await self.active_connections[user_id].send_text(message_json)
                return True
            except Exception as e:
                print(f"❌ [WebSocket Manager] Ошибка отправки сообщения пользователю {user_id}: {e}")
                self.disconnect(user_id)
                return False
        else:
            print(f"❌ [WebSocket Manager] User {user_id} not found in active connections")
        return False
    
    async def send_to_taxipark(self, message: dict, taxipark_id: int, exclude_user: str = None):
        """Отправить сообщение всем пользователям таксопарка"""
        print(f"🔍 [WebSocket Manager] send_to_taxipark called with taxipark_id: {taxipark_id} (type: {type(taxipark_id)})")
        print(f"🔍 [WebSocket Manager] taxipark_connections keys: {list(self.taxipark_connections.keys())}")
        
        if taxipark_id is None or taxipark_id not in self.taxipark_connections:
            print(f"❌ [WebSocket Manager] Taxipark {taxipark_id} not found in connections")
            return
        
        sent_count = 0
        for user_id in self.taxipark_connections[taxipark_id]:
            if exclude_user and user_id == exclude_user:
                continue
            
            if await self.send_personal_message(message, user_id):
                sent_count += 1
        
        print(f"📤 Сообщение отправлено {sent_count} пользователям таксопарка {taxipark_id}")
        return sent_count
    
    async def send_to_driver(self, message: dict, driver_id: str):
        """Отправить сообщение конкретному водителю"""
        return await self.send_personal_message(message, f"driver_{driver_id}")
    
    async def send_to_dispatcher(self, message: dict, dispatcher_id: str):
        """Отправить сообщение конкретному диспетчеру"""
        return await self.send_personal_message(message, f"dispatcher_{dispatcher_id}")
    
    async def broadcast_new_order(self, order_data: dict, taxipark_id: int, target_driver_id: int = None):
        """Отправить новый заказ водителям таксопарка"""
        message = {
            "type": "new_order",
            "data": order_data,
            "timestamp": datetime.now().isoformat()
        }
        
        if target_driver_id:
            # Отправляем конкретному водителю
            await self.send_to_driver(message, str(target_driver_id))
        else:
            # Отправляем всем водителям таксопарка
            await self.send_to_taxipark(message, taxipark_id)
    
    async def broadcast_order_status_update(self, order_data: dict, taxipark_id: int):
        """Отправить обновление статуса заказа диспетчерам"""
        message = {
            "type": "order_status_update",
            "data": order_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.send_to_taxipark(message, taxipark_id)
    
    def get_connection_count(self) -> int:
        """Получить количество активных соединений"""
        return len(self.active_connections)
    
    def get_taxipark_connections_count(self, taxipark_id: int) -> int:
        """Получить количество соединений в таксопарке"""
        if taxipark_id in self.taxipark_connections:
            return len(self.taxipark_connections[taxipark_id])
        return 0

# Глобальный экземпляр менеджера WebSocket
websocket_manager = WebSocketManager()
