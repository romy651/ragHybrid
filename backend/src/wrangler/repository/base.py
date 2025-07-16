from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..repository.store import Store


T = TypeVar("T")

class BaseRepository(ABC, Generic[T]):
    """
    Base repository class to manage the database connection and create the database tables
    """
    def __init__(self, store: Store):
        self.store = store

    @abstractmethod
    async def create(self, item: T) -> T:
        """create a new entity in the database"""
        pass
    
    @abstractmethod
    async def get_by_id(self, id: int) -> T | None:
        """get an entity by its id"""
        pass
    
    @abstractmethod
    async def update(self, item: T) -> T:
        """update an entity in the database"""
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        """delete an entity from the database"""
        pass
    
    @abstractmethod
    async def list_all(self, limit: int | None = None, offset: int | None = None) -> list[T]:
        """list all entities in the database"""
        pass