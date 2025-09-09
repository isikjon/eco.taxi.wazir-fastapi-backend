from fastapi import APIRouter, HTTPException, status, Request, Depends
from sqlalchemy.orm import Session
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import AuthService
from app.database.session import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/health")
async def auth_health_check():
    return {"status": "healthy", "service": "auth-service", "version": "2.0.0"}

@router.get("/test")
async def auth_test():
    return {"message": "Auth router is working!", "endpoint": "/auth/test"}

@router.post("/superadmin/login", response_model=LoginResponse)
async def superadmin_login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    print(f"\n🔐 AUTH: ===== LOGIN ATTEMPT START =====")
    print(f"🔐 AUTH: Request URL: {request.url}")
    print(f"🔐 AUTH: Request method: {request.method}")
    print(f"🔐 AUTH: Request headers: {dict(request.headers)}")
    print(f"🔐 AUTH: Login attempt for user: {login_data.login}")
    print(f"🔐 AUTH: Request data: {login_data}")
    print(f"🔐 AUTH: Request validation passed")
    
    try:
        # Используем AuthService для аутентификации
        result = await AuthService.authenticate_superadmin(db, login_data)
        print(f"✅ AUTH: Login successful for {login_data.login}")
        print(f"✅ AUTH: Returning success response")
        print(f"🔐 AUTH: ===== LOGIN ATTEMPT SUCCESS =====")
        return result
        
    except HTTPException as e:
        print(f"❌ AUTH: Login failed for {login_data.login}: {e.detail}")
        print(f"🔐 AUTH: ===== LOGIN ATTEMPT FAILED =====")
        raise e
    except Exception as e:
        print(f"❌ AUTH: Unexpected error during login: {str(e)}")
        print(f"🔐 AUTH: ===== LOGIN ATTEMPT FAILED =====")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )
