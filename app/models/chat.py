from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Literal

class MessageBase(BaseModel):
    content: str
    role: Literal["user", "assistant"]
    
class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: str
    conversation_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True  # Para permitir la conversión desde objetos ORM

class ConversationBase(BaseModel):
    title: Optional[str] = None
    
class ConversationCreate(ConversationBase):
    user_id: str  # ID del usuario que crea la conversación

class Conversation(ConversationBase):
    id: str
    created_at: datetime
    updated_at: datetime
    user_id: str
    
    class Config:
        from_attributes = True  # Para permitir la conversión desde objetos ORM

class ConversationWithFirstMessage(BaseModel):
    title: Optional[str] = None
    message_content: str
    user_id: Optional[str] = None