from pydantic import BaseModel, EmailStr
from typing import Optional

class ClientBase(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    email: Optional[str] = None
    preferred_payment_method: Optional[str] = "cash"

class ClientCreate(ClientBase):
    pass

class ClientLogin(BaseModel):
    phone_number: str
    sms_code: str

class ClientResponse(ClientBase):
    id: int
    rating: float
    total_rides: int
    total_spent: float
    is_active: bool
    
    class Config:
        from_attributes = True
