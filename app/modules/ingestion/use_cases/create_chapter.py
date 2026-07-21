from app.modules.ingestion.dtos import CreateChapterDto, GetChapterDto
from app.modules.ingestion.models.chapter import ChapterStatus, SourceType
from app.modules.ingestion.repositories.chapter_repository import ChapterRepository


def _segment_text(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n\n") if p.strip()]


class CreateChapterUseCase:
    def __init__(self, repository: ChapterRepository) -> None:
        self._repository = repository

    async def execute(self, payload: CreateChapterDto) -> GetChapterDto:
        chapter = await self._repository.create(
            child_id=payload.child_id,
            subject=payload.subject,
            school_start_date=payload.school_start_date,
        )

        for source_in in payload.sources:
            await self._repository.create_source(
                chapter,
                SourceType(source_in.type),
                source_in.raw_ref,
            )

        text_sources = [s for s in payload.sources if s.type == SourceType.text]
        non_text_sources = [s for s in payload.sources if s.type != SourceType.text]

        if non_text_sources and not text_sources:
            # OCR e scraping ainda não implementados — spec 01, seção 9 (pergunta em aberto)
            chapter.status = ChapterStatus.failed
            chapter.reason_code = "not_implemented"
        else:
            all_segments: list[str] = []
            for source in text_sources:
                all_segments.extend(_segment_text(source.raw_ref))
            chapter.segments = all_segments
            chapter.status = ChapterStatus.ready

        await self._repository.save(chapter)

        return GetChapterDto(
            chapter_id=chapter.id,
            child_id=chapter.child_id,
            subject=chapter.subject,
            school_start_date=chapter.school_start_date,
            status=chapter.status,
            segments=chapter.segments or None,
            reason_code=chapter.reason_code,
        )
