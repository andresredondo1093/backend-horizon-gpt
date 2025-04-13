# Este archivo hace que la carpeta core sea reconocida como un paquete Python
from app.core.config import settings

# Exportar los módulos relevantes
__all__ = ["settings"]