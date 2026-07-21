from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from app.core.config import get_settings
from app.core.db import TORTOISE_ORM

app = FastAPI(title="Smart App API", version="0.0.1")

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=False,  # schema é sempre via migração Aerich, nunca auto-gerado em runtime
    add_exception_handlers=True,
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check — usado pelo harness para confirmar que o ambiente sobe corretamente."""
    settings = get_settings()
    return {"status": "ok", "env": settings.environment}


# Routers dos motores são registrados aqui conforme cada spec é implementada.
# Exemplo (ainda não implementado — ver specs/03-evidence-engine.md):
# from app.engines.evidence.router import router as evidence_router
# app.include_router(evidence_router, prefix="/children", tags=["evidence"])
