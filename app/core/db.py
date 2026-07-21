from app.config.settings import get_settings

settings = get_settings()

# Cada módulo registra seu models/<entity>.py aqui conforme for implementado.
MODEL_MODULES = [
    "aerich.models",
    "app.modules.ingestion.models.chapter",
    # "app.modules.knowledge.models.node",
    # "app.modules.evidence.models.evidence",
    # "app.modules.learning_state.models.state",
    # "app.modules.generation.models.generation",
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
