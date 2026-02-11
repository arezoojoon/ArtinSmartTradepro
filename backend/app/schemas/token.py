from typing import Optional
from pydantic import BaseModel
from uuid import UUID

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    tenant_id: Optional[str] = None
    role: Optional[str] = None
    type: Optional[str] = None  # access, refresh, password_reset
