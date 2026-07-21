from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from app.core.config import get_settings
from app.core.db import TORTOISE_ORM

from app.engines.ingestion.router import router as ingestion_router

app = FastAPI(title="Smart App API", version="0.0.1")

_settings = get_settings()
# generate_schemas=True apenas em SQLite (testes em memória); em produção o Aerich gerencia.
_generate_schemas = _settings.database_url.startswith("sqlite")

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=_generate_schemas,
    add_exception_handlers=True,
)


app.include_router(ingestion_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check — usado pelo harness para confirmar que o ambiente sobe corretamente."""
    settings = get_settings()
    return {"status": "ok", "env": settings.environment}


# Routers dos motores são registrados aqui conforme cada spec é implementada.
# Exemplo (ainda não implementado — ver specs/03-evidence-engine.md):
# from app.engines.evidence.router import router as evidence_router
# app.include_router(evidence_router, prefix="/children", tags=["evidence"])
