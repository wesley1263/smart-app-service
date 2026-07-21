import os

# Precisa ser setado ANTES de app.core.db (e portanto app.main) ser importado,
# para que os testes rodem contra sqlite in-memory e não exijam Postgres real.
# O ciclo de vida do Tortoise (init/close) fica a cargo do register_tortoise
# em app/main.py, disparado pelos eventos de startup/shutdown do FastAPI —
# por isso os testes devem usar `with TestClient(app) as client:` (ver
# tests/test_health.py), nunca `TestClient(app)` solto.
os.environ.setdefault("DATABASE_URL", "sqlite://:memory:")
