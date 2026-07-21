from typing import Any
from uuid import UUID

from app.modules.common.abstracts.repository import CRUDRepository
from app.modules.ingestion.models.chapter import IngestedChapter, RawSource, SourceType


class ChapterRepository(CRUDRepository):
    async def create(self, **kwargs: Any) -> IngestedChapter:
        return await IngestedChapter.create(**kwargs)

    async def get_by_id(self, entity_id: UUID) -> IngestedChapter | None:
        return await IngestedChapter.get_or_none(id=entity_id)

    async def create_source(
        self, chapter: IngestedChapter, source_type: SourceType, raw_ref: str
    ) -> RawSource:
        return await RawSource.create(chapter=chapter, type=source_type, raw_ref=raw_ref)

    async def save(self, chapter: IngestedChapter) -> IngestedChapter:
        await chapter.save()
        return chapter
