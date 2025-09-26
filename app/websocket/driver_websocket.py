from fastapi import WebSocket, WebSocketDisconnect
from app.websocket.manager import websocket_manager
import json

async def driver_websocket_endpoint(websocket: WebSocket, driver_id: str):
    """WebSocket endpoint для водителей"""
    try:
        await websocket_manager.connect(
            websocket=websocket,
            user_id=f"driver_{driver_id}",
            user_type="driver",
            taxipark_id=None  # Будет получен из данных водителя
        )
        
        print(f"✅ [WebSocket] Водитель {driver_id} подключен")
        
        while True:
            try:
                # Ожидаем сообщения от клиента
                data = await websocket.receive_text()
                message = json.loads(data)
                
                print(f"🔍 [WebSocket] Получено сообщение от водителя {driver_id}: {message}")
                
                # Обрабатываем различные типы сообщений
                if message.get('type') == 'ping':
                    await websocket.send_text(json.dumps({
                        'type': 'pong',
                        'timestamp': message.get('timestamp')
                    }))
                elif message.get('type') == 'location_update':
                    # Обрабатываем обновление местоположения
                    await websocket_manager.send_to_taxipark(
                        {
                            'type': 'driver_location_update',
                            'driver_id': driver_id,
                            'location': message.get('location'),
                            'timestamp': message.get('timestamp')
                        },
                        message.get('taxipark_id')
                    )
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"❌ [WebSocket] Ошибка обработки сообщения от водителя {driver_id}: {e}")
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'message': str(e)
                }))
                
    except WebSocketDisconnect:
        print(f"🔍 [WebSocket] Водитель {driver_id} отключился")
    except Exception as e:
        print(f"❌ [WebSocket] Ошибка WebSocket для водителя {driver_id}: {e}")
    finally:
        websocket_manager.disconnect(f"driver_{driver_id}")
        print(f"❌ [WebSocket] Водитель {driver_id} отключен")
