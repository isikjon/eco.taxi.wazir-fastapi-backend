from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database.init_db import init_database
from app.api.auth.routes import router as auth_router
from app.api.superadmin.routes import router as superadmin_router

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
    print(f"\n🌐 INCOMING REQUEST: {request.method} {request.url}")
    print(f"🌐 Headers: {dict(request.headers)}")
    
    if request.method == "POST":
        try:
            body_bytes = await request.body()
            if body_bytes:
                body_str = body_bytes.decode('utf-8')
                print(f"🌐 Request body: {body_str}")
        except Exception as e:
            print(f"🌐 Error reading body: {e}")
    
    response = await call_next(request)
    
    print(f"🌐 RESPONSE STATUS: {response.status_code}")
    print(f"🌐 RESPONSE HEADERS: {dict(response.headers)}")
    
    return response

app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем роутеры СРАЗУ после создания приложения
print("🔧 Including auth router...")
print(f"  📍 Auth router prefix: {auth_router.prefix}")
print(f"  📍 Auth router tags: {auth_router.tags}")
print(f"  📍 Auth router routes: {len(auth_router.routes)}")

# Подробное логирование auth роутера
for route in auth_router.routes:
    if hasattr(route, 'path'):
        print(f"    🔗 {route.methods} {route.path} -> {route.name}")

app.include_router(auth_router)

print("🔧 Including superadmin router...")
print(f"  📍 Superadmin router prefix: {superadmin_router.prefix}")
print(f"  📍 Superadmin router tags: {superadmin_router.tags}")
print(f"  📍 Superadmin router routes: {len(superadmin_router.routes)}")

# Подробное логирование superadmin роутера
for route in superadmin_router.routes:
    if hasattr(route, 'path'):
        print(f"    🔗 {route.methods} {route.path} -> {route.name}")

app.include_router(superadmin_router)

print("✅ All routers included successfully")
print(f"🔍 Total app routes after including routers: {len(app.routes)}")

# Проверка работоспособности роутеров
print("\n🔍 Проверка auth роутера...")
auth_routes = [route for route in app.routes if hasattr(route, 'path') and '/auth' in str(route.path)]
print(f"  📍 Найдено auth роутов: {len(auth_routes)}")
for route in auth_routes:
    if hasattr(route, 'path'):
        print(f"    🔗 {route.methods} {route.path}")

print("\n🔍 Проверка superadmin роутера...")
superadmin_routes = [route for route in app.routes if hasattr(route, 'path') and '/superadmin' in str(route.path)]
print(f"  📍 Найдено superadmin роутов: {len(superadmin_routes)}")
for route in superadmin_routes:
    if hasattr(route, 'path'):
        print(f"    🔗 {route.methods} {route.path}")

# Теперь определяем endpoints ПОСЛЕ подключения роутеров
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
    print("\n🔍 DEBUG: Listing all registered routes...")
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            route_info = {
                "path": route.path,
                "methods": getattr(route, 'methods', []),
                "name": getattr(route, 'name', 'Unknown')
            }
            routes.append(route_info)
            print(f"  📍 {route_info['methods']} {route_info['path']} -> {route_info['name']}")
    
    print(f"🔍 Total routes found: {len(routes)}")
    
    print("\n🔍 DEBUG: Checking router objects...")
    print(f"  📍 Auth router: {auth_router}")
    print(f"  📍 Superadmin router: {superadmin_router}")
    
    return {"routes": routes, "total": len(routes)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8081,
        reload=True,
        log_level="info"
    )
