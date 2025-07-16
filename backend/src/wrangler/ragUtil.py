import hashlib
import mimetypes
from pathlib import Path
from typing import ClassVar
import os
import asyncio
from markitdown import MarkItDown
import tiktoken
from wrangler.model.chunk import Chunk
from wrangler.model.document import Document
from wrangler.model.product import Product
from wrangler.repository.analytic import Analytic
from wrangler.repository.chunk import ChunkRepository
from wrangler.repository.document import DocumentRepository
from wrangler.repository.store import Store

default_file_directory = Path("src/data")
default_store_directory = Path("src/store/rag.sqlite")

class RAGUtils:
    """
    FileReader class to read the file and parse it
    """
    extensions: ClassVar[list[str]] = [".csv", ".md"]
    
    def __init__(self, store_directory: Path = default_store_directory, 
                file_directory: Path = default_file_directory):
        if not store_directory.exists():
            store_directory.parent.mkdir(parents=True, exist_ok=True)
        self.store = Store(store_directory)
        self.analytic = Analytic()
        self.document_repository = DocumentRepository(self.store)
        self.chunk_repository = ChunkRepository(self.store)
        self.file_directory = file_directory
        
    @staticmethod
    async def parse_file(file_path: Path):
        try:
            reader = MarkItDown()
            # Use asyncio.to_thread to handle the blocking MarkItDown operation
            result = await asyncio.to_thread(reader.convert, file_path)
            return result.text_content
        except Exception as e:
            raise ValueError(f"Failed to parse file {file_path}: {e}")
        
    def get_file_list(self) -> list[Path]:
        files_list = []
        for file_name in os.listdir(self.file_directory):
            file_path = os.path.join(self.file_directory, file_name) 
            if os.path.isfile(file_path):
                files_list.append(Path(file_path))
        return files_list
    
    async def check_or_create_document(self, file_path: Path) -> str:
        """
        Check if the document already exists in the database and create it if it doesn't
        """
        uri = file_path.absolute().as_uri()
        
        file_bytes = file_path.read_bytes()
        
        md5_hash =  hashlib.md5(file_bytes).hexdigest()
        
        exist_document = await self.get_document_by_uri(uri)
        if exist_document and exist_document.metadata.get("md5") == md5_hash:
            return exist_document
        
        content = await self.parse_file(file_path)
        content_type, _ = mimetypes.guess_type(str(file_path))
        
        if not content_type:
            content_type = "text/plain"
        metadata = { "contentType": content_type, "md5": md5_hash }
        
        if exist_document is not None:
            exist_document.content = content
            exist_document.metadata = metadata
            return await self.document_repository.update(exist_document)
        
        await self.document_repository.create(Document(uri=uri, content=content, metadata=metadata or {}))
        if file_path.suffix.lower() == ".csv":
            self.analytic.create_product(file_path)
    
    async def ask(self, query: str) -> str:
        """
        Ask the RAGUtils to answer the query
        """
        return "Hello, World, you can start now now"
    
    def search(self, query:str, limit:int = 5, k: int = 60) -> list[tuple[Chunk, float]]:
        """
        Search the RAGUtils to find the most relevant documents
        """
        return self.chunk_repository.search_chunks_hybrid(query, limit, k)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()
    
    async def get_document_by_uri(self, uri: str) -> Document | None:
        return await self.document_repository.get_by_uri(uri)
    
    async def close(self):
        self.store.close()

