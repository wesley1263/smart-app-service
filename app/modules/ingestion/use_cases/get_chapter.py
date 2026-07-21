from uuid import UUID

from app.modules.common.exceptions.use_case_exception import UseCaseException
from app.modules.ingestion.dtos import GetChapterDto
from app.modules.ingestion.repositories.chapter_repository import ChapterRepository


class GetChapterUseCase:
    def __init__(self, repository: ChapterRepository) -> None:
        self._repository = repository

    async def execute(self, chapter_id: UUID) -> GetChapterDto:
        chapter = await self._repository.get_by_id(chapter_id)
        if chapter is None:
            raise UseCaseException("Chapter not found", status_code=404)
        return GetChapterDto(
            chapter_id=chapter.id,
            child_id=chapter.child_id,
            subject=chapter.subject,
            school_start_date=chapter.school_start_date,
            status=chapter.status,
            segments=chapter.segments or None,
            reason_code=chapter.reason_code,
        )
