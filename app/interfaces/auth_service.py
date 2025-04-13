from abc import ABC, abstractmethod
from typing import Optional
from app.models.user import Token, UserLogin, UserBase

class AuthServiceInterface(ABC):
    """
    Interfaz que define las operaciones requeridas para un servicio de autenticación.
    Siguiendo el principio de segregación de interfaces (SOLID), esta interfaz
    contiene solo los métodos relacionados con la autenticación.
    """
    
    @abstractmethod
    async def authenticate_user(self, user_data: UserLogin) -> Optional[UserBase]:
        """Autentica a un usuario y retorna sus datos si las credenciales son válidas"""
        pass
    
    @abstractmethod
    async def create_access_token(self, data: dict) -> Token:
        """Crea un token de acceso para el usuario autenticado"""
        pass
    
    @abstractmethod
    async def verify_token(self, token: str) -> Optional[dict]:
        """Verifica la validez de un token y retorna los datos del usuario"""
        pass