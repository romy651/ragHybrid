import os
from .base import BaseEmbedder
from openai import AsyncOpenAI

class OpenAIEmbedder(BaseEmbedder):
    _model: str = "text-embedding-3-small"
    _vector_dim: int = 1536

    def __init__(self, model: str = _model, vector_dim: int = _vector_dim):
        super().__init__(model, vector_dim)

    async def embed(self, text: str) -> list[float]:
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = await client.embeddings.create(input=text, model=self._model)
        return response.data[0].embedding
    