from pydantic import BaseModel
from typing import Optional

class DispatcherLoginRequest(BaseModel):
    login: str
    password: str

class DispatcherLoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    redirect_url: Optional[str] = None
    taxipark_id: Optional[int] = None
    taxipark_name: Optional[str] = None
