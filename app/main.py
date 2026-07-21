from fastapi import FastAPI
from loguru import logger
from tortoise.contrib.fastapi import register_tortoise

from app.config.settings import get_settings
from app.core.db import TORTOISE_ORM
from app.core.middlewares import setup_cors
from app.core.routers import include_routers

settings = get_settings()
_generate_schemas = settings.database_url.startswith("sqlite")


def create_app() -> FastAPI:
    logger.info("Creating application...")

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        debug=settings.debug,
    )

    register_tortoise(
        application,
        config=TORTOISE_ORM,
        generate_schemas=_generate_schemas,
        add_exception_handlers=True,
    )

    setup_cors(application)
    include_routers(application)

    return application


app = create_app()
