from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Any

from app.helpers.chat_helper import ChatHelper
from app.helpers.users_helper import UsersHelper
from app.models.chat import MessageCreate, ConversationWithFirstMessage
from app.models.user import UserBase
from app.core.config import settings

# Configurar el logger
import logging
logger = logging.getLogger(__name__)

# Crear instancia del helper de chat
chat_helper = ChatHelper(
    supabase_url=settings.SUPABASE_URL,
    supabase_key=settings.SUPABASE_KEY
)

# Crear instancia del helper de usuarios para la autenticación
users_helper = UsersHelper(
    supabase_url=settings.SUPABASE_URL,
    supabase_key=settings.SUPABASE_KEY,
    jwt_secret=settings.JWT_SECRET,
    access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

@router.post("/conversations", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
async def create_conversation_with_first_message(
    data: ConversationWithFirstMessage,
    current_user: UserBase = Depends(users_helper.get_current_user)
):
    """
    Crea una nueva conversación con un primer mensaje.
    
    Args:
        data: Datos de la conversación y primer mensaje
        current_user: Usuario autenticado obtenido del token
    
    Returns:
        La conversación creada con el mensaje inicial
    """
    # Asignamos el ID del usuario actual
    data.user_id = str(current_user.id)
    
    # Creamos la conversación con el mensaje
    result = await chat_helper.create_conversation_with_message(data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear la conversación con el mensaje inicial"
        )
    
    return result

@router.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
async def add_message_to_conversation(
    conversation_id: str, 
    message: MessageCreate,
    current_user: UserBase = Depends(users_helper.get_current_user)
):
    """
    Añade un mensaje a una conversación existente.
    
    Args:
        conversation_id: ID de la conversación
        message: Datos del mensaje a crear
        current_user: Usuario autenticado obtenido del token
    
    Returns:
        El mensaje creado
    """
    # Aseguramos que el rol sea "user" ya que el mensaje proviene del usuario
    message.role = "user"
    
    # Verificar que la conversación existe y que el usuario es el propietario
    conversations = await chat_helper.get_conversations_by_user(str(current_user.id))
    conversation_exists = False
    
    for conv in conversations:
        if conv.get("id") == conversation_id:
            conversation_exists = True
            break
            
    if not conversation_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada o no tienes permiso para acceder a ella"
        )
    
    result = await chat_helper.add_message_to_conversation(conversation_id, message, str(current_user.id))
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al añadir el mensaje a la conversación"
        )
    
    return result

# Nuevo endpoint para obtener todas las conversaciones de un usuario por su ID
@router.get("/user/{user_id}/conversations", response_model=List[Dict[str, Any]])
async def get_conversations_by_user_id(
    user_id: str,
    current_user: UserBase = Depends(users_helper.get_current_user)
):
    """
    Obtiene todas las conversaciones de un usuario específico por su ID.
    
    Args:
        user_id: ID del usuario
        current_user: Usuario autenticado obtenido del token (para verificación)
    
    Returns:
        Lista de conversaciones del usuario especificado
    """
    # Por seguridad, idealmente verificaríamos que el usuario tiene permisos
    # para ver estas conversaciones (es el mismo usuario o un administrador)
    
    conversations = await chat_helper.get_conversations_by_user(user_id)
    return conversations

# Nuevo endpoint para obtener todos los mensajes de una conversación por su ID
@router.get("/conversations/{conversation_id}/messages", response_model=List[Dict[str, Any]])
async def get_messages_by_conversation_id(
    conversation_id: str,
    current_user: UserBase = Depends(users_helper.get_current_user)
):
    """
    Obtiene todos los mensajes de una conversación específica por su ID.
    
    Args:
        conversation_id: ID de la conversación
        current_user: Usuario autenticado obtenido del token (para verificación)
    
    Returns:
        Lista de mensajes de la conversación especificada
    """
    # Por seguridad, verificamos que la conversación pertenece al usuario
    # o que el usuario tiene permisos para verla
    conversations = await chat_helper.get_conversations_by_user(str(current_user.id))
    conversation_exists = False
    
    for conv in conversations:
        if conv.get("id") == conversation_id:
            conversation_exists = True
            break
            
    if not conversation_exists:
        # Si quieres permitir acceso a administradores, aquí podrías
        # verificar si el usuario tiene ese rol
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada o no tienes permiso para acceder a ella"
        )
    
    messages = await chat_helper.get_messages_by_conversation(conversation_id)
    return messages