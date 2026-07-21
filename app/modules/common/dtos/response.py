from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    data: T | None = None
    count: int | None = None
    total: int | None = None
    description: str | None = None
    status: int
