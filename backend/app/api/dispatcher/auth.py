from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.dispatcher_auth_service import DispatcherAuthService
from app.schemas.dispatcher_auth import DispatcherLoginRequest, DispatcherLoginResponse

templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/auth", tags=["dispatcher-auth"])

@router.get("/login", response_class=HTMLResponse)
async def dispatcher_login_page(request: Request):
    return templates.TemplateResponse("dispatcher/login.html", {"request": request})

@router.post("/login", response_model=DispatcherLoginResponse)
async def dispatcher_login(login_data: DispatcherLoginRequest, db: Session = Depends(get_db)):
    return await DispatcherAuthService.authenticate_dispatcher(db, login_data)
