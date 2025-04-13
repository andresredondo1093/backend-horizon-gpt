import logging
import uuid
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional

from app.models.chat import (
    Conversation, ConversationCreate, 
    Message, MessageCreate,
    ConversationWithFirstMessage
)
from app.core.config import settings

logger = logging.getLogger(__name__)

class ChatHelper:
    def __init__(self, supabase_url: str, supabase_key: str):
        """Inicializa el helper con la configuración de Supabase."""
        import supabase
        self.supabase = supabase.create_client(supabase_url, supabase_key)
        logger.info("ChatHelper inicializado con cliente Supabase")
        
    async def create_conversation_with_message(self, data: ConversationWithFirstMessage) -> Optional[Dict]:
        """
        Crea una nueva conversación y el primer mensaje en la misma.
        
        Args:
            data (ConversationWithFirstMessage): Datos de la conversación y primer mensaje
            
        Returns:
            Dict: Datos de la conversación creada con el mensaje, o None si falla
        """
        try:
            # Crear ID único para la conversación
            conversation_id = str(uuid.uuid4())
            current_time = datetime.now().isoformat()
            
            # Preparar datos de la conversación
            conversation_data = {
                "id": conversation_id,
                "title": data.title,
                "user_id": data.user_id,
                "created_at": current_time,
                "updated_at": current_time
            }
            
            # Crear la conversación en Supabase
            result = self.supabase.table("conversations").insert(conversation_data).execute()
            
            if not result.data:
                logger.error("Error al crear la conversación")
                return None
            
            # Preparar datos del mensaje
            message_id = str(uuid.uuid4())
            message_data = {
                "id": message_id,
                "conversation_id": conversation_id,
                "content": data.message_content,
                "role": "user",  # El primer mensaje siempre es del usuario
                "created_at": current_time
            }
            
            # Crear el mensaje en Supabase
            message_result = self.supabase.table("messages").insert(message_data).execute()
            
            if not message_result.data:
                # Si falla la creación del mensaje, intentar eliminar la conversación
                self.supabase.table("conversations").delete().eq("id", conversation_id).execute()
                logger.error("Error al crear el mensaje inicial")
                return None
            
            # Procesar el mensaje con el LLM a través de n8n
            llm_response = await self._process_message_with_llm(data.message_content, conversation_id)
            if llm_response:
                # Guardar la respuesta del LLM como un nuevo mensaje
                llm_message_id = str(uuid.uuid4())
                llm_message_data = {
                    "id": llm_message_id,
                    "conversation_id": conversation_id,
                    "content": llm_response,
                    "role": "assistant",  # La respuesta siempre es del asistente
                    "created_at": datetime.now().isoformat()
                }
                
                # Crear el mensaje de respuesta en Supabase
                self.supabase.table("messages").insert(llm_message_data).execute()
                
                # Devolver los datos combinados
                return {
                    "conversation": conversation_data,
                    "user_message": message_data,
                    "llm_response": llm_message_data
                }
            
            # Devolver los datos combinados
            return {
                "conversation": conversation_data,
                "message": message_data
            }
            
        except Exception as e:
            logger.error(f"Error al crear conversación con mensaje: {str(e)}")
            return None
            
    async def add_message_to_conversation(self, conversation_id: str, message: MessageCreate, user_id: str) -> Optional[Dict]:
        """
        Añade un mensaje a una conversación existente.
        
        Args:
            conversation_id (str): ID de la conversación
            message (MessageCreate): Datos del mensaje a crear
            user_id (str): ID del usuario que envía el mensaje
            
        Returns:
            Dict: Datos del mensaje creado y la respuesta del LLM, o None si falla
        """
        try:
            # Verificar que la conversación existe
            conversation = self.supabase.table("conversations").select("*").eq("id", conversation_id).execute()
            
            if not conversation.data:
                logger.error(f"Conversación {conversation_id} no encontrada")
                return None
                
            # Preparar datos del mensaje
            message_id = str(uuid.uuid4())
            current_time = datetime.now().isoformat()
            
            message_data = {
                "id": message_id,
                "conversation_id": conversation_id,
                "content": message.content,
                "role": message.role,  # Usamos el rol proporcionado (debería ser "user")
                "created_at": current_time
            }
            
            # Crear el mensaje en Supabase
            result = self.supabase.table("messages").insert(message_data).execute()
            
            if not result.data:
                logger.error("Error al crear el mensaje")
                return None
                
            # Actualizar el timestamp de la conversación
            self.supabase.table("conversations").update(
                {"updated_at": current_time}
            ).eq("id", conversation_id).execute()
            
            # Procesar el mensaje con el LLM a través de n8n
            llm_response = await self._process_message_with_llm(message.content, conversation_id)
            if llm_response:
                # Guardar la respuesta del LLM como un nuevo mensaje
                llm_message_id = str(uuid.uuid4())
                llm_message_data = {
                    "id": llm_message_id,
                    "conversation_id": conversation_id,
                    "content": llm_response,
                    "role": "assistant",  # La respuesta siempre es del asistente
                    "created_at": datetime.now().isoformat()
                }
                
                # Crear el mensaje de respuesta en Supabase
                self.supabase.table("messages").insert(llm_message_data).execute()
                
                # Devolver tanto el mensaje del usuario como la respuesta del LLM
                return {
                    "user_message": message_data,
                    "llm_response": llm_message_data
                }
            
            return message_data
            
        except Exception as e:
            logger.error(f"Error al añadir mensaje a conversación: {str(e)}")
            return None
    
    async def _process_message_with_llm(self, user_message: str, conversation_id: str) -> Optional[str]:
        """
        Procesa el mensaje del usuario con el LLM a través de n8n.
        
        Args:
            user_message (str): Mensaje del usuario
            conversation_id (str): ID de la conversación
            
        Returns:
            str: Respuesta del LLM, o None si hay un error
        """
        try:
            # URL del webhook de n8n
            webhook_url = "https://n8n-n8n.crt53y.easypanel.host/webhook/send-message"
            
            # Preparar payload
            payload = {
                "message": user_message,
                "id": conversation_id
            }
            
            # Realizar la llamada al webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        logger.info(f"Respuesta de n8n recibida: {response_data}")
                        
                        # Extraer la respuesta del LLM del resultado
                        if isinstance(response_data, dict) and "message" in response_data:
                            # Nuevo formato {'message': '...'}
                            return response_data["message"]
                        else:
                            logger.warning(f"Formato de respuesta inesperado: {response_data}")
                            return str(response_data)
                    else:
                        logger.error(f"Error al llamar al webhook de n8n: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error al procesar mensaje con LLM: {str(e)}")
            return None
            
    async def get_conversations_by_user(self, user_id: str) -> List[Dict]:
        """Obtiene todas las conversaciones de un usuario."""
        try:
            result = self.supabase.table("conversations").select("*").eq("user_id", user_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error al obtener conversaciones del usuario: {str(e)}")
            return []
            
    async def get_messages_by_conversation(self, conversation_id: str) -> List[Dict]:
        """Obtiene todos los mensajes de una conversación específica."""
        try:
            result = self.supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error al obtener mensajes de la conversación: {str(e)}")
            return []