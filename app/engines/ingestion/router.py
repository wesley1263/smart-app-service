from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.engines.ingestion import schemas, service

router = APIRouter(prefix="/chapters", tags=["ingestion"])


@router.post("", response_model=schemas.ChapterResponse, status_code=201)
async def create_chapter(payload: schemas.ChapterCreateRequest) -> schemas.ChapterResponse:
    chapter = await service.create_chapter(payload)
    return schemas.ChapterResponse(
        chapter_id=chapter.id,
        child_id=chapter.child_id,
        subject=chapter.subject,
        school_start_date=chapter.school_start_date,
        status=chapter.status,
        segments=chapter.segments or None,
        reason_code=chapter.reason_code,
    )


@router.get("/{chapter_id}", response_model=schemas.ChapterResponse)
async def get_chapter(chapter_id: UUID) -> schemas.ChapterResponse:
    chapter = await service.get_chapter(chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return schemas.ChapterResponse(
        chapter_id=chapter.id,
        child_id=chapter.child_id,
        subject=chapter.subject,
        school_start_date=chapter.school_start_date,
        status=chapter.status,
        segments=chapter.segments or None,
        reason_code=chapter.reason_code,
    )
