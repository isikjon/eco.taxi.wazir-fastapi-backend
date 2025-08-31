try:
    from app.api.auth.routes import router as auth_router
    print("✅ Auth router imported successfully")
    print(f"Auth router prefix: {auth_router.prefix}")
    print(f"Auth router tags: {auth_router.tags}")
except Exception as e:
    print(f"❌ Error importing auth router: {e}")

try:
    from app.api.superadmin.routes import router as superadmin_router
    print("✅ Superadmin router imported successfully")
    print(f"Superadmin router prefix: {superadmin_router.prefix}")
    print(f"Superadmin router tags: {superadmin_router.tags}")
except Exception as e:
    print(f"❌ Error importing superadmin router: {e}")

try:
    from app.services.auth_service import AuthService
    print("✅ AuthService imported successfully")
except Exception as e:
    print(f"❌ Error importing AuthService: {e}")

try:
    from app.schemas.auth import LoginRequest, LoginResponse
    print("✅ Auth schemas imported successfully")
except Exception as e:
    print(f"❌ Error importing auth schemas: {e}")
