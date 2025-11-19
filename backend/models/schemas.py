from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    session_id: str
    persona: str = "general"

class ChatResponse(BaseModel):
    content: str
