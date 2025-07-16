from datetime import datetime
from pydantic import BaseModel, Field


class Document(BaseModel):
    id: int | None = None
    content: str
    uri: str | None = None
    metadata: dict = {}
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)