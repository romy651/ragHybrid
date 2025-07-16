import json
import re
from typing import ClassVar

import tiktoken
from .base import BaseRepository
from ..repository.store import Store
from ..model.chunk import Chunk
from ..embedding import get_embedder

class Chunker:
    """Chunker class to chunk the document into smaller chunks"""
    
    encoder: ClassVar[tiktoken.Encoding] = tiktoken.get_encoding("cl100k_base")
    
    def __init__(self, chunk_size: int = 256, chunk_overlap: int = 32):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    async def chunk(self, text: str) -> list[str]:
        """Chunk the text into smaller chunks"""
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]
        
        tokens = self.encoder.encode(text, disallowed_special=())
        if self.chunk_size > len(tokens):
            return [text]
        
        chunks = []
        i = 0
        
        while i < len(tokens):
            start_idx = i
            end_idx = min(i + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start_idx:end_idx]
            chunk_text = self.encoder.decode(chunk_tokens)
            chunks.append(chunk_text)
            if end_idx >= len(tokens):
                break
            i += self.chunk_size - self.chunk_overlap
        return chunks
    
chunker = Chunker() 

class ChunkRepository(BaseRepository[Chunk]):
    """
    Chunk repository class to manage the database connection and create the database tables
    """
    def __init__(self, store):
        super().__init__(store)
        self.embedder = get_embedder()
    
    async def create(self, item: Chunk, commit: bool = True) -> Chunk:
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        
        cursor = self.store._connection.cursor()
        cursor.execute(
            """
            INSERT INTO chunks (document_id, content, metadata)
            VALUES (?, ?, ?)
            """,
            (item.document_id, item.content, json.dumps(item.metadata))
        )
        item.id = cursor.lastrowid

        embedding = await self.embedder.embed(item.content)
        serialized_embedding = Store.serialize_embeddings(embedding)
        cursor.execute(
            """
            INSERT INTO chunk_embeddings (chunk_id, embedding)
            VALUES (?, ?)
            """,
            (item.id, serialized_embedding)
        )
        
        cursor.execute(
            """
            INSERT INTO chunks_fts (rowid, content)
            VALUES (?, ?)
            """,
            (item.id, item.content)
        )
        
        if commit:
            self.store._connection.commit()
        return item
    
    async def get_by_id(self, id: int) -> Chunk | None:
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        
        cursor = self.store._connection.cursor()
        cursor.execute(
            """
            SELECT id, document_id, content, metadata
            FROM chunks
            WHERE id = ?
            """,
            (id,)
        )
        result = cursor.fetchone()
        if result is None:
            return None
        
        chunk_id, document_id, content, metadata = result
        return Chunk(
            id=chunk_id,
            document_id=document_id,
            content=content,
            metadata=json.loads(metadata)
        )
    
    async def update(self, item: Chunk) -> Chunk:
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        
        cursor = self.store._connection.cursor()
        cursor.execute(
            """
            UPDATE chunks SET document_id = ?, content = ?, metadata = ? WHERE id = ?""",
            (item.document_id, item.content, json.dumps(item.metadata), item.id)
        )
        
        #regenerate embedding
        embedding = await self.embedder.embed(item.content)
        serialized_embedding = Store.serialize_embeddings(embedding)
        cursor.execute(
            """
            UPDATE chunks_embeddings SET embedding = ? WHERE chunk_id = ?""",
            (serialized_embedding, item.id)
        )
        
        #update fts
        cursor.execute(
            """
            UPDATE chunks_fts SET content = ? WHERE rowid = ?""",
            (item.content, item.id)
        )

        self.store._connection.commit()
        return item
    
    async def delete(self, id: int, commit: bool = True) -> bool:
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        
        cursor = self.store._connection.cursor()

        #delete fts first
        cursor.execute(
            """
            DELETE FROM chunks_fts WHERE rowid = ?""",
            (id,)
        )

        #delete embedding
        cursor.execute(
            """
            DELETE FROM chunks_embeddings WHERE chunk_id = ?""",
            (id,)
        )

        #delete chunk
        cursor.execute(
            """
            DELETE FROM chunks WHERE id = ?""",
            (id,)
        )
        if commit:
            self.store._connection.commit()
        return True
    
    async def list_all(self, limit: int | None = None, offset: int | None = None) -> list[Chunk]:
        """list all chunks in the database"""
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        
        cursor = self.store._connection.cursor()
        query = """
            SELECT id, document_id, content, metadata
            FROM chunks
            ORDER BY document_id DESC
        """
        if limit is not None:
            query += " LIMIT ?"
        if offset is not None:
            query += " OFFSET ?"
        cursor.execute(query, (limit, offset))

        result = cursor.fetchall()
        return [Chunk(
            id=chunk_id,
            document_id=document_id,
            content=content,
            metadata=json.loads(metadata) if metadata else {}
        ) for chunk_id, document_id, content, metadata in result]
    
    async def create_chunks_from_document(self, document_id: int, content: str, commit: bool = True) -> list[Chunk]:
        """create chunks and embeddings from a document"""
        chunk_texts = await chunker.chunk(content)
        created_chunks = []

        for order, chunk_text in enumerate(chunk_texts):
            chunk = Chunk(document_id=document_id, content=chunk_text, metadata={"order": order})
            created_chunk = await self.create(chunk, commit)
            created_chunks.append(created_chunk)
        return created_chunks
    
    async def delete_all(self, commit: bool = True) -> bool:
        """delete all chunks"""
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        
        cursor = self.store._connection.cursor()
        cursor.execute("DELETE FROM chunks")
        cursor.execute("DELETE FROM chunks_embeddings")
        cursor.execute("DELETE FROM chunks_fts")
        if commit:
            self.store._connection.commit()
        return True
    
    async def get_by_document_id(self, document_id: int) -> list[Chunk]:
        """get all chunks by document id"""
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        
        cursor = self.store._connection.cursor()
        cursor.execute("""
            SELECT c.id, c.document_id, c.content, c.metadata, d.uri, d.metadata as document_metadata
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE c.document_id = ?
            ORDER BY JSON_EXTRACT(c.metadata, '$.order')
            """, (document_id,))
        result = cursor.fetchall()
        return [Chunk(
            id=chunk_id,
            document_id=document_id,
            content=content,
            metadata=json.loads(metadata) if metadata else {},
            document_uri=document_uri,
            document_metadata=json.loads(document_metadata) if document_metadata else {}
        ) for chunk_id, document_id, content, metadata, document_uri, document_metadata in result]

    async def delete_by_document_id(self, document_id: int, commit: bool = True) -> bool:
        """delete all chunks by document id"""
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        
        chunks = await self.get_by_document_id(document_id)

        delete_any = False
        for chunk in chunks:
            if chunk.id is not None:
                deleted = await self.delete(chunk.id, commit=False)
                delete_any = deleted or delete_any
        
        if commit and delete_any:
            self.store._connection.commit()
        return delete_any
    
    async def search_chunks(self, query: str, limit: int = 5) -> list[tuple[Chunk, float]]:
        """search chunks by content and similarity"""
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        
        query_embedding = await self.embedder.embed(query)
        serialized_embedding = Store.serialize_embeddings(query_embedding)

        cursor = self.store._connection.cursor()
        cursor.execute("""
            SELECT c.id, c.document_id, c.content, c.metadata, d.uri, d.metadata as document_metadata
            FROM chunks_embeddings ce
            JOIN chunks c ON ce.chunk_id = c.id
            JOIN documents d ON c.document_id = d.id
            WHERE embedding MATCH ? AND k = ?
            """, (serialized_embedding, limit))
        result = cursor.fetchall()

        return [ 
            (
                Chunk(
                    id=chunk_id,
                    document_id=document_id,
                    content=content,
                    metadata=json.loads(metadata) if metadata else {},
                    document_uri=document_uri,
                    document_metadata=json.loads(document_metadata) if document_metadata else {}
                ), 
                1.0 / (1.0 + distance)
            ) 
            for chunk_id, document_id, content, metadata, document_uri, document_metadata, distance in result
        ]
    
    async def search_chunks_fts(self, query: str, limit: int = 5) -> list[tuple[Chunk, float]]:
        """search chunks by using full text search"""
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        
        cursor = self.store._connection.cursor()

        # Remove special characters and split into words
        words = re.findall(r"\b\w+\b", query.lower())
        # Join with OR to find chunks containing any of the keywords
        fts_query = " OR ".join(words) if words else query

        cursor.execute(
            """
            SELECT c.id, c.document_id, c.content, c.metadata, d.uri, d.metadata as document_metadata
            FROM chunks_fts
            JOIN chunks c ON chunks_fts.rowid = c.id
            JOIN documents d ON c.document_id = d.id
            WHERE content MATCH ? 
            ORDER BY rank
            LIMIT ?
            """, (fts_query, limit))
        result = cursor.fetchall()

        return [
            (
                Chunk(
                    id=chunk_id,
                    document_id=document_id,
                    content=content,
                    metadata=json.loads(metadata) if metadata else {},
                    document_uri=document_uri,
                    document_metadata=json.loads(document_metadata) if document_metadata else {}
                ), 
                - rank
            )
            for chunk_id, document_id, content, metadata, document_uri, document_metadata, rank in result
        ]
    
    async def search_chunks_hybrid(self, query: str, limit: int = 5, k: int = 5) -> list[tuple[Chunk, float]]:
        """search chunks by using hybrid search"""
        if self.store._connection is None:
            raise ValueError("Store connection is not open")
        
        cursor = self.store._connection.cursor()
        
        query_embedding = await self.embedder.embed(query)
        serialized_embedding = Store.serialize_embeddings(query_embedding)

        words = re.findall(r"\b\w+\b", query.lower())
        fts_query = " OR ".join(words) if words else query

        cursor.execute(
            """
            WITH vector_search AS (
                SELECT
                    c.id,
                    c.document_id,
                    c.content,
                    c.metadata,
                    ROW_NUMBER() OVER (ORDER BY ce.distance) as vector_rank
                FROM chunk_embeddings ce
                JOIN chunks c ON c.id = ce.chunk_id
                WHERE ce.embedding MATCH :embedding AND k = :k_vector
                ORDER BY ce.distance
            ),
            fts_search AS (
                SELECT
                    c.id,
                    c.document_id,
                    c.content,
                    c.metadata,
                    ROW_NUMBER() OVER (ORDER BY chunks_fts.rank) as fts_rank
                FROM chunks_fts
                JOIN chunks c ON c.id = chunks_fts.rowid
                WHERE chunks_fts MATCH :fts_query
                ORDER BY chunks_fts.rank
            ),   
            all_chunks AS (
                SELECT id, document_id, content, metadata FROM vector_search
                UNION
                SELECT id, document_id, content, metadata FROM fts_search
            ),
            rrf_scores AS (
                SELECT
                    a.id,
                    a.document_id,
                    a.content,
                    a.metadata,
                    COALESCE(1.0 / (:k + v.vector_rank), 0) + COALESCE(1.0 / (:k + f.fts_rank), 0) as rrf_score
                FROM all_chunks a
                LEFT JOIN vector_search v ON a.id = v.id
                LEFT JOIN fts_search f ON a.id = f.id
            )
            SELECT r.id, r.document_id, r.content, r.metadata, r.rrf_score, d.uri, d.metadata as document_metadata
            FROM rrf_scores r
            JOIN documents d ON r.document_id = d.id
            ORDER BY r.rrf_score DESC
            LIMIT :limit
            """,
            {
                "embedding": serialized_embedding,
                "k_vector": limit * 3,
                "fts_query": fts_query,
                "k": k,
                "limit": limit
            }
        )

        result = cursor.fetchall()

        return [
            (
                Chunk(
                    id=chunk_id,
                    document_id=document_id,
                    content=content,
                    metadata=json.loads(metadata) if metadata else {},
                    document_uri=document_uri,
                    document_metadata=json.loads(document_metadata) if document_metadata else {}
                ), 
                rrf_score
            )
            for chunk_id, document_id, content, metadata, rrf_score, document_uri, document_metadata in result
        ]
    