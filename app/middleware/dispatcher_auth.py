from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from app.core.security import verify_token
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.administrator import Administrator

async def check_dispatcher_auth(request: Request, call_next):
    # Пропускаем маршруты авторизации и статические файлы
    if (request.url.path.startswith('/disp/') and 
        not request.url.path.startswith('/disp/auth') and 
        not request.url.path.startswith('/static/')):
        
        token = request.cookies.get('dispatcher_token') or request.headers.get('authorization', '').replace('Bearer ', '')
        
        if not token:
            return RedirectResponse(url='/disp/auth/login', status_code=302)
        
        try:
            payload = verify_token(token)
            if payload.get('role') != 'dispatcher':
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверный тип токена"
                )
            
            db = next(get_db())
            administrator = db.query(Administrator).filter(Administrator.id == payload.get('sub')).first()
            
            if not administrator or not administrator.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Аккаунт неактивен"
                )
            
            request.state.dispatcher = administrator
            request.state.taxipark_id = administrator.taxipark_id
            
        except Exception as e:
            return RedirectResponse(url='/disp/auth/login', status_code=302)
    
    response = await call_next(request)
    return response
