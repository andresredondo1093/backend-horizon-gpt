# Este archivo hace que la carpeta routers sea reconocida como un paquete Python
from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router

# Exportar los routers relevantes
__all__ = ["auth_router", "chat_router"]