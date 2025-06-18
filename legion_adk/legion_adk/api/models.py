# legion_adk/api/models.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# KEEP: Existing Pydantic models for API compatibility 
class Message(BaseModel):
    id: Optional[str] = None
    content: str
    role: str  # 'user' or 'assistant'
    timestamp: Optional[str] = None

class Chat(BaseModel):
    chatId: str
    title: str
    createdAt: str
    messages: List[Message] = []