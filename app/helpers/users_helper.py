from typing import Optional, Dict, Any, List
import httpx
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import logging
from app.models.user import UserBase, UserCreate, UserLogin, Token
from app.interfaces.user_repository import UserRepositoryInterface
from app.interfaces.auth_service import AuthServiceInterface

logger = logging.getLogger(__name__)

class UsersHelper(UserRepositoryInterface, AuthServiceInterface):
    def __init__(self, supabase_url=None, supabase_key=None, jwt_secret=None, algorithm="HS256", access_token_expire_minutes=60*24):
        # Permitir inicialización desde variables de entorno o parámetros
        self.SUPABASE_URL = supabase_url or os.getenv("SUPABASE_URL")
        self.SUPABASE_KEY = supabase_key or os.getenv("SUPABASE_KEY") 
        self.JWT_SECRET = jwt_secret or os.getenv("JWT_SECRET")
        self.ALGORITHM = algorithm
        self.ACCESS_TOKEN_EXPIRE_MINUTES = access_token_expire_minutes
        
        # Configuración para el hash de contraseñas
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # OAuth2 para la autenticación
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
        
    # Funciones de utilidad para autenticación
    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return self.pwd_context.hash(password)

    # Implementaciones de AuthServiceInterface
    async def authenticate_user(self, user_data: UserLogin) -> Optional[UserBase]:
        # Intentamos autenticar primero por username y luego por email si está disponible
        user = await self.get_user_by_username(user_data.username)
        
        if not user and user_data.email:
            user = await self.get_user_by_email(user_data.email)
        
        if not user:
            return None
            
        # Verificar la contraseña
        if not self.verify_password(user_data.password, user.hashed_password):
            return None
            
        return user
        
    async def create_access_token(self, data: dict, user_id: str = None) -> Token:
        expires_delta = timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.JWT_SECRET, algorithm=self.ALGORITHM)
        
        return Token(access_token=encoded_jwt, token_type="bearer", user_id=user_id)
        
    async def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.JWT_SECRET, algorithms=[self.ALGORITHM])
            return payload
        except JWTError:
            return None
    
    # Implementaciones de UserRepositoryInterface
    async def get_user_by_id(self, user_id: int) -> Optional[UserBase]:
        headers = {
            "apikey": self.SUPABASE_KEY,
            "Authorization": f"Bearer {self.SUPABASE_KEY}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.SUPABASE_URL}/rest/v1/users?id=eq.{user_id}&select=*",
                headers=headers
            )
            
            if response.status_code == 200 and response.json():
                return UserBase(**response.json()[0])
            return None
            
    async def get_user_by_email(self, email: str) -> Optional[UserBase]:
        headers = {
            "apikey": self.SUPABASE_KEY,
            "Authorization": f"Bearer {self.SUPABASE_KEY}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.SUPABASE_URL}/rest/v1/users?email=eq.{email}&select=*",
                headers=headers
            )
            
            if response.status_code == 200 and response.json():
                return UserBase(**response.json()[0])
            return None

    # Mantener compatibilidad con código existente
    async def get_user_by_username(self, username: str) -> Optional[UserBase]:
        headers = {
            "apikey": self.SUPABASE_KEY,
            "Authorization": f"Bearer {self.SUPABASE_KEY}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.SUPABASE_URL}/rest/v1/users?username=eq.{username}&select=*",
                headers=headers
            )
            
            if response.status_code == 200 and response.json():
                return UserBase(**response.json()[0])
            return None

    async def create_user(self, user: UserCreate) -> UserBase:
        headers = {
            "apikey": self.SUPABASE_KEY,
            "Authorization": f"Bearer {self.SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        hashed_password = self.get_password_hash(user.password)
        
        user_data = {
            "username": user.username,
            "email": user.email,
            "hashed_password": hashed_password
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.SUPABASE_URL}/rest/v1/users",
                json=user_data,
                headers=headers
            )
            
            if response.status_code == 201:
                return UserBase(**response.json()[0])
            return None
    
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserBase]:
        headers = {
            "apikey": self.SUPABASE_KEY,
            "Authorization": f"Bearer {self.SUPABASE_KEY}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.SUPABASE_URL}/rest/v1/users?select=*&offset={skip}&limit={limit}",
                headers=headers
            )
            
            if response.status_code == 200:
                return [UserBase(**user) for user in response.json()]
            return []
            
    async def update_user(self, user_id: int, user_data: dict) -> Optional[UserBase]:
        headers = {
            "apikey": self.SUPABASE_KEY,
            "Authorization": f"Bearer {self.SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.SUPABASE_URL}/rest/v1/users?id=eq.{user_id}",
                json=user_data,
                headers=headers
            )
            
            if response.status_code == 200 and response.json():
                return UserBase(**response.json()[0])
            return None
            
    async def delete_user(self, user_id: int) -> bool:
        headers = {
            "apikey": self.SUPABASE_KEY,
            "Authorization": f"Bearer {self.SUPABASE_KEY}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.SUPABASE_URL}/rest/v1/users?id=eq.{user_id}",
                headers=headers
            )
            
            return response.status_code == 204
    
    # Dependencia para obtener el usuario actual
    async def get_current_user(self, token: str = Depends(OAuth2PasswordBearer(tokenUrl="login"))):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, self.JWT_SECRET, algorithms=[self.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        user = await self.get_user_by_username(username)
        if user is None:
            raise credentials_exception
        return user