from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class BaseRepository(ABC):
    """Contrato base para todos os repositórios."""


class CreateRepositoryMixin(ABC):
    @abstractmethod
    async def create(self, **kwargs: Any) -> Any:
        raise NotImplementedError


class RetrieveRepositoryMixin(ABC):
    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Any | None:
        raise NotImplementedError


class CRUDRepository(
    CreateRepositoryMixin,
    RetrieveRepositoryMixin,
    BaseRepository,
    ABC,
):
    """Mixin de conveniência que combina Create + Retrieve."""
