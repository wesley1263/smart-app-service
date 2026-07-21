from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class RawSourceIn(BaseModel):
    type: Literal["image", "link", "text"]
    raw_ref: str


class CreateChapterDto(BaseModel):
    child_id: UUID
    subject: str
    school_start_date: date
    sources: list[RawSourceIn]


class GetChapterDto(BaseModel):
    chapter_id: UUID
    child_id: UUID
    subject: str
    school_start_date: date
    status: str
    segments: list[str] | None = None
    reason_code: str | None = None
