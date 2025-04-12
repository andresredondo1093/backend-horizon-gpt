from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv
import logging

# Configurar el logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log") if os.path.exists(os.path.dirname(os.path.abspath(__file__))) else logging.StreamHandler(),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de la aplicación
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 día

# Inicializar la aplicación FastAPI
app = FastAPI(
    title="Backend de Proyecto Horizon",
    description="API para la autenticación de usuarios",
    version="0.1.0"
)

# Configurar CORS
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración para el hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 para la autenticación
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Modelos Pydantic
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Funciones de utilidad para autenticación
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    
    return encoded_jwt

# Funciones para interactuar con Supabase
async def get_user_by_username(username: str):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&select=*",
            headers=headers
        )
        
        if response.status_code == 200 and response.json():
            return response.json()[0]
        return None

async def create_user(username: str, email: str, hashed_password: str):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    user_data = {
        "username": username,
        "email": email,
        "hashed_password": hashed_password
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/users",
            json=user_data,
            headers=headers
        )
        
        if response.status_code == 201:
            return response.json()[0]
        return None

# Dependencia para obtener el usuario actual
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

# Endpoints de la API
@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"********************************************************")
    print(f"Intentando iniciar sesión con usuario: {form_data.username}")
    print(f"Intentando iniciar sesión con usuario: {form_data.password}")
    print(f"Intentando iniciar sesión con usuario: {form_data.grant_type}")
    print(f"Intentando iniciar sesión con usuario: {form_data.client_id}")
    print(f"Intentando iniciar sesión con usuario: {form_data.client_secret}")
    print(f"Intentando iniciar sesión con usuario: {form_data.scopes}")
    print(f"********************************************************")
    logger.info(f"Intentando iniciar sesión con usuario: {form_data.username}")
    user = await get_user_by_username(form_data.username)
    print(f"********************************************************")
    print(f"Intentando iniciar sesión con usuario: {user}")
    print(f"********************************************************")
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register")
async def register_user(user: UserCreate):
    # Verificar si el usuario ya existe
    existing_user = await get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado"
        )
    
    # Hash de la contraseña
    hashed_password = get_password_hash(user.password)
    
    # Crear el usuario
    new_user = await create_user(user.username, user.email, hashed_password)
    
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el usuario"
        )
    
    return {"message": "Usuario registrado exitosamente"}

@app.get("/me", response_model=Dict[str, Any])
async def read_users_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    # Quitar la contraseña hasheada de la respuesta
    user_data = {k: v for k, v in current_user.items() if k != "hashed_password"}
    return user_data

@app.get("/")
async def root():
    return {"message": "Bienvenido a la API del Proyecto Horizon"}

# Iniciar el servidor
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)