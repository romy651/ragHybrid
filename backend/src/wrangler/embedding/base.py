class BaseEmbedder:
    _model_name: str = ""
    _vector_dim: int = 0

    def __init__(self, model_name: str, vector_dim: int):
        self._model_name = model_name
        self._vector_dim = vector_dim
    
    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_model_name(self) -> str:
        return self._model_name
    
    def get_vector_dim(self) -> int:
        return self._vector_dim
    