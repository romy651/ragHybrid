from pathlib import Path
import struct
import sqlite_vec
import sqlite3

from ..embedding import get_embedder


class Store: 
    """
    Store class to manage the database connection and create the database tables
    """
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._connection = self.create_db()

    def create_db(self) -> sqlite3.Connection:
        """
        Create the database tables
        """
        db = sqlite3.connect(self.db_path)
        db.enable_load_extension(True)
        sqlite_vec.load(db)

        # if not exists we create the table documents
        db.execute("""CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                content TEXT NOT NULL,
                uri TEXT, 
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # if not exists we create the table chunks
        db.execute("""CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)

        embedder = get_embedder()
        db.execute(f"""CREATE VIRTUAL TABLE IF NOT EXISTS chunk_embeddings USING vec0(
                chunk_id INTEGER PRIMARY KEY,
                embedding FLOAT[{embedder._vector_dim}]
                )
        """)

        # for full text search
        db.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                content,
                content='chunks',
                content_rowid='id'
                )
        """)
        
        # index for better performance 
        db.execute("""CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)""")

        db.commit()

        return db
    
    @staticmethod
    def serialize_embeddings(embeddings: list[float]) -> bytes:
        """
        Serialize the embeddings to a binary format
        """
        return struct.pack(f"{len(embeddings)}f", *embeddings)
    
    def close(self) -> None:
        """
        Close the database connection
        """
        if self._connection is not None:
            self._connection.close()
            self._connection = None





