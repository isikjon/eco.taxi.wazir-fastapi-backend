from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TaxiParkBase(BaseModel):
    name: str
    commission_percent: float = 15.0


class TaxiParkCreate(TaxiParkBase):
    pass


class TaxiParkUpdate(BaseModel):
    name: Optional[str] = None
    commission_percent: Optional[float] = None
    income: Optional[float] = None
    drivers_count: Optional[int] = None
    dispatchers_count: Optional[int] = None
    is_active: Optional[bool] = None


class TaxiParkResponse(TaxiParkBase):
    id: int
    created_at: datetime
    income: float
    drivers_count: int
    dispatchers_count: int
    is_active: bool
    
    class Config:
        from_attributes = True


class TaxiParkList(BaseModel):
    id: int
    name: str
    created_at: datetime
    income: float
    drivers_count: int
    dispatchers_count: int
    commission_percent: float
    is_active: bool
    
    class Config:
        from_attributes = True
