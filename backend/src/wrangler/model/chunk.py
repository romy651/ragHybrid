from pydantic import BaseModel


class Chunk(BaseModel):
    id: int | None = None
    document_id: int
    content: str
    metadata: dict = {}
    document_uri: str | None = None
    document_metadata: dict = {}
