from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Importar desde nuestra nueva estructura
from app.core.config import settings
from app.routers import auth_router, chat_router

# Configurar el logging
logger = logging.getLogger(__name__)

# Inicializar la aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Bienvenido a la API del Proyecto Horizon"}

# Iniciar el servidor
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)