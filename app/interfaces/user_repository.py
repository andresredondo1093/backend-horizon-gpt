from abc import ABC, abstractmethod
from typing import Optional, List
from app.models.user import UserBase, UserCreate

class UserRepositoryInterface(ABC):
    """
    Interfaz que define las operaciones requeridas para un repositorio de usuarios.
    Siguiendo el principio de inversión de dependencias (SOLID), las clases de alto nivel
    deberían depender de esta interfaz en lugar de implementaciones concretas.
    """
    
    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[UserBase]:
        """Obtiene un usuario por su ID"""
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[UserBase]:
        """Obtiene un usuario por su email"""
        pass
    
    @abstractmethod
    async def create_user(self, user: UserCreate) -> UserBase:
        """Crea un nuevo usuario"""
        pass
    
    @abstractmethod
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserBase]:
        """Obtiene una lista de usuarios con paginación"""
        pass
    
    @abstractmethod
    async def update_user(self, user_id: int, user_data: dict) -> Optional[UserBase]:
        """Actualiza los datos de un usuario"""
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: int) -> bool:
        """Elimina un usuario por su ID"""
        pass