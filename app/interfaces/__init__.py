# Este archivo hace que la carpeta interfaces sea reconocida como un paquete Python
# Aquí exportaremos las interfaces para facilitar su importación desde otros módulos

from app.interfaces.user_repository import UserRepositoryInterface
from app.interfaces.auth_service import AuthServiceInterface

__all__ = ["UserRepositoryInterface", "AuthServiceInterface"]