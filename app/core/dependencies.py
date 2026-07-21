from app.config.settings import Settings, get_settings
from app.modules.ingestion.repositories.chapter_repository import ChapterRepository
from app.modules.ingestion.use_cases.create_chapter import CreateChapterUseCase
from app.modules.ingestion.use_cases.get_chapter import GetChapterUseCase


class DependencyInjectionContainer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    # --- ingestion ---

    def chapter_repository(self) -> ChapterRepository:
        return ChapterRepository()

    def create_chapter(self) -> CreateChapterUseCase:
        return CreateChapterUseCase(self.chapter_repository())

    def get_chapter(self) -> GetChapterUseCase:
        return GetChapterUseCase(self.chapter_repository())


container = DependencyInjectionContainer(get_settings())
