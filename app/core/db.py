from app.core.config import get_settings

settings = get_settings()

# Lista de módulos de models Tortoise. Cada motor adiciona seu app/engines/<nome>/models.py
# aqui conforme for implementado (ver AGENTS.md e specs/0X-*.md correspondente).
MODEL_MODULES = [
    "aerich.models",  # tabela interna de controle de migrações do Aerich
    # "app.engines.knowledge.models",
    # "app.engines.evidence.models",
    # "app.engines.learning_state.models",
]

TORTOISE_ORM = {
    "connections": {"default": settings.database_url},
    "apps": {
        "models": {
            "models": MODEL_MODULES,
            "default_connection": "default",
        },
    },
}
