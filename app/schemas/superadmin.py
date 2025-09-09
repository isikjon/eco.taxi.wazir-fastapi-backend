from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SuperAdminBase(BaseModel):
    login: str = Field(..., min_length=1, description="Логин суперадмина")
    position: str = Field(..., min_length=1, description="Должность суперадмина")

class SuperAdminCreate(SuperAdminBase):
    password: str = Field(..., min_length=1, description="Пароль суперадмина")

class SuperAdminUpdate(BaseModel):
    login: Optional[str] = None
    position: Optional[str] = None
    is_active: Optional[bool] = None

class SuperAdminResponse(SuperAdminBase):
    id: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SuperAdminList(BaseModel):
    superadmins: list[SuperAdminResponse]
    total: int
