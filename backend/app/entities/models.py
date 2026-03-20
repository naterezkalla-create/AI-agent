from pydantic import BaseModel
from typing import Any, Optional, Dict, List
from datetime import datetime


class EntityCreate(BaseModel):
    type: str
    data: Dict[str, Any]


class EntityUpdate(BaseModel):
    data: Dict[str, Any]


class EntityResponse(BaseModel):
    id: str
    user_id: str
    type: str
    data: Dict[str, Any]
    created_at: str
    updated_at: str


class AutomationCreate(BaseModel):
    name: str
    cron_expression: str
    prompt: str
    enabled: bool = True
    user_id: str = "default"


class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    cron_expression: Optional[str] = None
    prompt: Optional[str] = None
    enabled: Optional[bool] = None
    user_id: Optional[str] = None


class MemoryNoteCreate(BaseModel):
    category: str
    key: str
    content: str
    confidence: float = 0.8
    source: str = "manual"
    review_status: str = "active"


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    tool_calls: List[Dict] = []
