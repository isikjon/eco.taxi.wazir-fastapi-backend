from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class OrderBase(BaseModel):
    client_name: str = Field(..., min_length=1, description="Имя клиента")
    client_phone: str = Field(..., min_length=10, description="Телефон клиента")
    pickup_address: str = Field(..., min_length=1, description="Адрес подачи")
    destination_address: str = Field(..., min_length=1, description="Адрес назначения")
    price: float = Field(..., gt=0, description="Стоимость заказа")
    status: str = Field(default="completed", description="Статус заказа")
    driver_id: Optional[int] = Field(None, description="ID водителя")

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    pickup_address: Optional[str] = None
    destination_address: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = None
    driver_id: Optional[int] = None

class OrderResponse(OrderBase):
    id: int
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
