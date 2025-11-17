from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Each model here maps to a collection (lowercased class name)

class AuditSession(BaseModel):
    user_id: Optional[str] = Field(default=None, description="Optional user identifier")
    transcript: List[dict] = Field(default_factory=list, description="Q/A turns with the agent")
    report: Optional[dict] = Field(default=None, description="Generated strategic report")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
