from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings

async def authenticate_user(db: AsyncSession, login: str, password: str) -> dict | None:
    if login == settings.ADMIN_LOGIN and password == settings.ADMIN_PASSWORD:
        return {
            "id": 1,
            "login": login,
            "role": "admin",
            "is_active": True
        }
    return None

async def get_user_by_login(db: AsyncSession, login: str) -> dict | None:
    if login == settings.ADMIN_LOGIN:
        return {
            "id": 1,
            "login": login,
            "role": "admin",
            "is_active": True
        }
    return None
