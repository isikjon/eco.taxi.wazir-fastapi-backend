from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database.init_db import init_database
from app.api.auth.routes import router as auth_router
from app.api.superadmin.routes import router as superadmin_router
from app.api.dispatcher.routes import router as dispatcher_router
from app.api.driver.routes import router as driver_router
from app.websocket.routes import router as websocket_router
from app.websocket.driver_websocket import driver_websocket_endpoint
from app.middleware.dispatcher_auth import check_dispatcher_auth

# Импортируем API endpoints для мобильного приложения
from api import get_parks, send_sms_code, login_driver, register_driver, check_driver_status
from app.api.client import client_router
from api_balance import router as balance_router
from api_driver_profile import router as driver_profile_router
from api_photo_control import router as photo_control_router

# Инициализируем FCM сервис при запуске
print("🔍 [MAIN] Инициализация FCM сервиса...")
try:
    from app.services.fcm_service import fcm_service
    print("✅ [MAIN] FCM сервис инициализирован")
except Exception as e:
    print(f"❌ [MAIN] Ошибка инициализации FCM сервиса: {e}")

init_database()

app = FastAPI(
    title="Taxi 2.0 API",
    description="Микросервисное такси приложение",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    
    if request.method == "POST":
        try:
            body_bytes = await request.body()
            if body_bytes:
                body_str = body_bytes.decode('utf-8')
                print(f"🌐 Request body: {body_str}")
        except Exception as e:
            print(f"🌐 Error reading body: {e}")
    
    response = await call_next(request)
    
    return response

@app.middleware("http")
async def dispatcher_auth_middleware(request: Request, call_next):
    return await check_dispatcher_auth(request, call_next)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


print("📋 Подключение роутов...")

app.include_router(auth_router)
app.include_router(superadmin_router)
app.include_router(dispatcher_router)
app.include_router(driver_router)
app.include_router(websocket_router)

app.add_api_route("/api/parks", get_parks, methods=["GET"], tags=["mobile-api"])
app.add_api_route("/api/sms/send", send_sms_code, methods=["POST"], tags=["mobile-api"])
app.add_api_route("/api/drivers/login", login_driver, methods=["POST"], tags=["mobile-api"])
app.add_api_route("/api/drivers/register", register_driver, methods=["POST"], tags=["mobile-api"])
app.add_api_route("/api/drivers/status", check_driver_status, methods=["GET"], tags=["mobile-api"])

app.include_router(balance_router, tags=["balance-api"])
app.include_router(driver_profile_router, tags=["driver-profile-api"])
app.include_router(photo_control_router, tags=["photo-control-api"])
app.include_router(client_router, tags=["client-api"])

app.get("/api/parks")(get_parks)
app.post("/api/sms/send")(send_sms_code)
app.post("/api/drivers/login")(login_driver)
app.post("/api/drivers/register")(register_driver)
app.get("/api/drivers/status")(check_driver_status)

print("✅ Роутеры подключены")

print("🔍 Проверка Devino 2FA API...")
try:
    import requests
    devino_api_url = "https://phoneverification.devinotele.com"
    
    test_response = requests.get(
        devino_api_url,
        timeout=5
    )
    
    if test_response.status_code in [200, 404, 405]:
        print("✅ Devino 2FA API доступен")
    else:
        print(f"⚠️ Devino 2FA API вернул HTTP {test_response.status_code}")
except requests.exceptions.Timeout:
    print("❌ Devino 2FA API не отвечает (timeout)")
except Exception as e:
    print(f"❌ Ошибка подключения к Devino 2FA API: {e}")

@app.get("/")
async def root():
    return RedirectResponse(url="/superadmin/login", status_code=302)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "taxi-2.0", "version": "2.0.0"}

@app.get("/test/auth")
async def test_auth():
    return {"message": "Auth router is working", "endpoint": "/test/auth"}

@app.get("/test/auth/direct")
async def test_auth_direct():
    return {"message": "Direct auth test", "auth_router_prefix": auth_router.prefix, "auth_routes_count": len(auth_router.routes)}

@app.get("/test/auth/simple")
async def test_auth_simple():
    return {"message": "Simple auth test", "status": "ok"}

@app.get("/debug/routes")
async def debug_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            route_info = {
                "path": route.path,
                "methods": getattr(route, 'methods', []),
                "name": getattr(route, 'name', 'Unknown')
            }
            routes.append(route_info)
    return {"routes": routes, "total": len(routes)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
        log_level="info"
    )
