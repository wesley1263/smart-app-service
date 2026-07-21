from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import container
from app.modules.common.dtos.response import Response
from app.modules.common.exceptions.use_case_exception import UseCaseException
from app.modules.ingestion.dtos import CreateChapterDto, GetChapterDto
from app.modules.ingestion.use_cases.create_chapter import CreateChapterUseCase
from app.modules.ingestion.use_cases.get_chapter import GetChapterUseCase

router = APIRouter(prefix="/api/v1/chapters", tags=["ingestion"])


@router.post(
    "",
    response_model=Response[GetChapterDto],
    status_code=status.HTTP_201_CREATED,
)
async def create_chapter(
    payload: CreateChapterDto,
    use_case: Annotated[CreateChapterUseCase, Depends(container.create_chapter)],
) -> Response[GetChapterDto]:
    result = await use_case.execute(payload)
    return Response(data=result, status=201, description="Chapter created")


@router.get(
    "/{chapter_id}",
    response_model=Response[GetChapterDto],
    status_code=status.HTTP_200_OK,
)
async def get_chapter(
    chapter_id: UUID,
    use_case: Annotated[GetChapterUseCase, Depends(container.get_chapter)],
) -> Response[GetChapterDto]:
    try:
        result = await use_case.execute(chapter_id)
        return Response(data=result, status=200, description="Chapter found")
    except UseCaseException as err:
        raise HTTPException(status_code=err.status_code, detail=err.message)
