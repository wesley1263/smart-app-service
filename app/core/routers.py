from fastapi import FastAPI
from loguru import logger


def include_routers(app: FastAPI) -> None:
    logger.info("Registering routes...")

    from app.modules.common.api.healthz import router as health_router
    from app.modules.ingestion.api.v1.routes import router as ingestion_router

    app.include_router(health_router)
    app.include_router(ingestion_router)
