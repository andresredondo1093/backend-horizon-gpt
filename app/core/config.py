import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# Cargar variables de entorno
load_dotenv()

# Obtener la ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Configurar el logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / "logs" / "app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Configuración de la aplicación
class Settings:
    PROJECT_NAME: str = "Proyecto Horizon API"
    PROJECT_VERSION: str = "0.1.0"
    PROJECT_DESCRIPTION: str = "API para la autenticación de usuarios"
    
    # Configuración de Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
    
    # Configuración JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 día
    
    # Configuración CORS
    CORS_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Crear una instancia de las configuraciones
settings = Settings()