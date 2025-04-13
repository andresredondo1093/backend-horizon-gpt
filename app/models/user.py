from pydantic import BaseModel, EmailStr
from typing import Optional

# Modelos Pydantic
class UserBase(BaseModel):
    id: Optional[str] = None
    username: str
    email: str
    hashed_password: Optional[str] = None

class UserCreate(UserBase):
    password: str
    hashed_password: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str
    email: Optional[str] = None  # Hacemos email opcional para mantener compatibilidad

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: Optional[str] = None