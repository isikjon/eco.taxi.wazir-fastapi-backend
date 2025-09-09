from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    login: str = Field(..., min_length=1, description="Логин пользователя")
    password: str = Field(..., min_length=1, description="Пароль пользователя")

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    redirect_url: str

class TokenData(BaseModel):
    sub: str
    role: str
