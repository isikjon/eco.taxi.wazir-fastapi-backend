from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi import HTTPException, status

from app.models.administrator import Administrator
from app.models.taxipark import TaxiPark
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.schemas.dispatcher_auth import DispatcherLoginRequest, DispatcherLoginResponse

class DispatcherAuthService:
    @staticmethod
    async def authenticate_dispatcher(db: Session, login_data: DispatcherLoginRequest) -> DispatcherLoginResponse:
        administrator = db.query(Administrator).filter(Administrator.login == login_data.login).first()
        
        if not administrator or not verify_password(login_data.password, administrator.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль"
            )
        
        if not administrator.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Аккаунт заблокирован"
            )
        
        taxipark = db.query(TaxiPark).filter(TaxiPark.id == administrator.taxipark_id).first()
        if not taxipark or not taxipark.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Таксопарк неактивен"
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(administrator.id), "role": "dispatcher", "taxipark_id": administrator.taxipark_id},
            expires_delta=access_token_expires
        )
        
        return DispatcherLoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            redirect_url="/disp/",
            taxipark_id=taxipark.id,
            taxipark_name=taxipark.name
        )
