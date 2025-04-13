# Este archivo hace que la carpeta app sea reconocida como un paquete Python
# Versión del proyecto
VERSION = "0.1.0"

# Implementamos lazy loading para evitar referencias circulares
# y mejorar la organización siguiendo principios SOLID

# Funciones para lazy loading de componentes
def get_settings():
    from app.core.config import settings
    return settings

def get_users_helper():
    from app.helpers.users_helper import UsersHelper
    return UsersHelper()

# Namespaces por dominio
from app.models import user
from app.routers import auth

# Exportación reducida a los módulos/namespaces en lugar de clases individuales
__all__ = [
    "get_settings",
    "get_users_helper",
    "user",    # Namespace para modelos de usuario
    "auth"     # Namespace para rutas de autenticación
]