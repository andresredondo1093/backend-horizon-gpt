from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import logging
from typing import Dict, Any

from app.helpers.users_helper import UsersHelper
from app.models.user import UserCreate, UserLogin, Token, UserBase
from app.core.config import settings

# Configurar el logger
logger = logging.getLogger(__name__)

# Crear instancia del helper de usuarios
users_helper = UsersHelper(
    supabase_url=settings.SUPABASE_URL,
    supabase_key=settings.SUPABASE_KEY,
    jwt_secret=settings.JWT_SECRET,
    access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(tags=["authentication"])

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"Intentando iniciar sesión con usuario: {form_data.username}")
    
    # Creamos un objeto UserLogin con el nombre de usuario
    user_login = UserLogin(username=form_data.username, password=form_data.password)
    user = await users_helper.authenticate_user(user_login)
    print(user)
    logger.info(f"Info user: {user}")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token de acceso
    access_token_data = {"sub": user.username}
    token = await users_helper.create_access_token(data=access_token_data, user_id=user.id)
    
    return token

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    # Verificar si el usuario ya existe
    existing_user = await users_helper.get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado"
        )
    
    # Crear el usuario usando la nueva interfaz
    new_user = await users_helper.create_user(user)
    
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el usuario"
        )
    
    return {"message": "Usuario registrado exitosamente", "user_id": new_user.id}

@router.get("/me", response_model=Dict[str, Any])
async def read_users_me(current_user: UserBase = Depends(users_helper.get_current_user)):
    # Convertir el modelo de usuario a un diccionario sin la contraseña hasheada
    user_dict = current_user.model_dump() if hasattr(current_user, 'model_dump') else dict(current_user)
    if "hashed_password" in user_dict:
        user_dict.pop("hashed_password")
    return user_dict