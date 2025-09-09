from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AdministratorBase(BaseModel):
    login: str
    first_name: str
    last_name: str
    taxipark_id: int


class AdministratorCreate(AdministratorBase):
    password: str


class AdministratorUpdate(BaseModel):
    login: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    taxipark_id: Optional[int] = None
    is_active: Optional[bool] = None


class AdministratorResponse(AdministratorBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AdministratorList(BaseModel):
    id: int
    login: str
    first_name: str
    last_name: str
    taxipark_id: int
    taxipark_name: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
