from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi import HTTPException, status

from app.models.superadmin import SuperAdmin
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.schemas.auth import LoginRequest, LoginResponse

class AuthService:
    @staticmethod
    async def authenticate_superadmin(db: Session, login_data: LoginRequest) -> LoginResponse:
        superadmin = db.query(SuperAdmin).filter(SuperAdmin.login == login_data.login).first()
        
        if not superadmin or not verify_password(login_data.password, superadmin.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль"
            )
        
        if not superadmin.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Аккаунт заблокирован"
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(superadmin.id), "role": "superadmin"},
            expires_delta=access_token_expires
        )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            redirect_url="/superadmin/dashboard"
        )
