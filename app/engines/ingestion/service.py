from uuid import UUID

from app.engines.ingestion.models import ChapterStatus, IngestedChapter, RawSource, SourceType
from app.engines.ingestion.schemas import ChapterCreateRequest


def _segment_text(text: str) -> list[str]:
    """Divide texto em parágrafos, filtrando linhas vazias."""
    return [p.strip() for p in text.split("\n\n") if p.strip()]


async def create_chapter(payload: ChapterCreateRequest) -> IngestedChapter:
    chapter = await IngestedChapter.create(
        child_id=payload.child_id,
        subject=payload.subject,
        school_start_date=payload.school_start_date,
    )

    for source_in in payload.sources:
        await RawSource.create(chapter=chapter, type=source_in.type, raw_ref=source_in.raw_ref)

    text_sources = [s for s in payload.sources if s.type == SourceType.text]
    non_text_sources = [s for s in payload.sources if s.type != SourceType.text]

    if non_text_sources and not text_sources:
        # OCR e scraping ainda não implementados — spec 01, seção 9 (pergunta em aberto)
        chapter.status = ChapterStatus.failed
        chapter.reason_code = "not_implemented"
        await chapter.save()
        return chapter

    all_segments: list[str] = []
    for source in text_sources:
        all_segments.extend(_segment_text(source.raw_ref))

    chapter.segments = all_segments
    chapter.status = ChapterStatus.ready
    await chapter.save()
    return chapter


async def get_chapter(chapter_id: UUID) -> IngestedChapter | None:
    return await IngestedChapter.get_or_none(id=chapter_id)
