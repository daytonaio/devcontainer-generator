from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DevContainer(BaseModel):
    id: Optional[int] = None
    url: str
    devcontainer_json: str
    devcontainer_url: Optional[str]
    repo_context: str
    tokens: int
    model: str
    embedding: Optional[str]
    generated: bool
    created_at: str = datetime.utcnow().isoformat()