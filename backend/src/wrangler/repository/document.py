from ..model.document import Document
from .base import BaseRepository
import json


class DocumentRepository(BaseRepository[Document]):
    
    
    def __init__(self, store, chunk_repository=None):
        super().__init__(store)
        if chunk_repository is None:
            from ..repository.chunk import ChunkRepository
            chunk_repository = ChunkRepository(store)
        self.chunk_repository = chunk_repository
    
    async def create(self, item: Document) -> Document:
        """create a new document and its chunks and embeddings"""
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        
        cursor = self.store._connection.cursor()
        cursor.execute("BEGIN TRANSACTION")

        try:
            cursor.execute("""
                        INSERT INTO documents (content, uri, metadata, created_at, updated_at) 
                        VALUES (?, ?, ?, ?, ?)
                        """, 
                        (item.content, 
                            item.uri, 
                            json.dumps(item.metadata), 
                            item.created_at, 
                            item.updated_at)
            )
            document_id = cursor.lastrowid

            assert document_id is not None, "Failed to create document in the database"
            item.id = document_id

            await self.chunk_repository.create_chunks_from_document(document_id, item.content, commit=False)
            cursor.execute("COMMIT")
            return item
        except Exception as e:
            cursor.execute("ROLLBACK")
            raise e

    async def get_by_id(self, id: int) -> Document | None:
        """get a document by its id"""
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        
        cursor = self.store._connection.cursor()
        cursor.execute("SELECT id, content, uri, metadata, created_at, updated_at FROM documents WHERE id = ?", (id,))
        result = cursor.fetchone()
        if result is None:
            return None
        document_id, content, uri, metadata, created_at, updated_at = result
        metadata = json.loads(metadata) if metadata else {}
        return Document(
            id=document_id,
            content=content,
            uri=uri,
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at
        )
    
    async def get_by_uri(self, uri: str) -> Document | None:
        """get a document by its uri"""
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        
        cursor = self.store._connection.cursor()
        cursor.execute("SELECT id, content, uri, metadata, created_at, updated_at FROM documents WHERE uri = ?", (uri,))
        result = cursor.fetchone()
        if result is None:
            return None
        document_id, content, uri, metadata, created_at, updated_at = result
        metadata = json.loads(metadata) if metadata else {}
        return Document(
            id=document_id,
            content=content,
            uri=uri,
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at
        )
    
    async def update(self, item: Document) -> Document:
        """update a document and its chunks and embeddings"""
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        if item.id is None:
            raise ValueError("Document id is required to update a document")
        
        cursor = self.store._connection.cursor()
        cursor.execute("BEGIN TRANSACTION")

        try:
            cursor.execute("""
                        UPDATE documents SET content = ?, uri = ?, metadata = ?, updated_at = ?
                        WHERE id = ?
                        """, (item.content, item.uri, json.dumps(item.metadata), item.updated_at, item.id))
            
            await self.chunk_repository.delete_by_document_id(item.id, commit=False)
            await self.chunk_repository.create_chunks_from_document(item.id, item.content, commit=False)

            cursor.execute("COMMIT")
            return item
        except Exception as e:
            cursor.execute("ROLLBACK")
            raise e
        
    async def delete(self, id: int) -> bool:
        """delete a document and its chunks and embeddings"""
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        cursor = self.store._connection.cursor()
        cursor.execute("DELETE FROM documents WHERE id = ?", (id,))
        deleted = cursor.rowcount > 0
        self.store._connection.commit()
        return deleted
    
    async def list_all(self, limit: int | None = None, offset: int | None = None) -> list[Document]:
        """list all documents"""
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        cursor = self.store._connection.cursor()
        query = "SELECT id, content, uri, metadata, created_at, updated_at FROM documents ORDER BY created_at DESC"
        params = {}
        if limit is not None:
            query += " LIMIT ?"
            params["limit"] = limit
        if offset is not None:
            query += " OFFSET ?"
            params["offset"] = offset
        cursor.execute(query, params)
        result = cursor.fetchall()
        return [
            Document(
                    id=document_id,
                    content=content,
                    uri=uri,
                    metadata=json.loads(metadata) if metadata else {},
                    created_at=created_at,
                    updated_at=updated_at
                )
                for document_id, content, uri, metadata, created_at, updated_at in result
        ]
        