from wrangler.embedding.base import BaseEmbedder
from .openai import OpenAIEmbedder

def get_embedder() -> BaseEmbedder:
    return OpenAIEmbedder()