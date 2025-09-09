from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DriverBase(BaseModel):
    first_name: str = Field(..., min_length=1, description="Имя водителя")
    last_name: str = Field(..., min_length=1, description="Фамилия водителя")
    phone: str = Field(..., min_length=10, description="Телефон водителя")
    car_model: str = Field(..., min_length=1, description="Модель автомобиля")
    car_number: str = Field(..., min_length=5, description="Номер автомобиля")
    balance: float = Field(default=0.0, description="Баланс водителя")
    is_active: bool = Field(default=True, description="Активен ли водитель")

class DriverCreate(DriverBase):
    pass

class DriverUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    car_model: Optional[str] = None
    car_number: Optional[str] = None
    balance: Optional[float] = None
    is_active: Optional[bool] = None

class DriverResponse(DriverBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
