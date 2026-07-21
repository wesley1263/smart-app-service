# ADR-0002 — Escolha de stack (backend)

**Status:** aceito

## Contexto
Precisamos de um stack que suporte: schemas semi-estruturados e versionados (Learning Nodes evoluem sem perder versões antigas), operações assíncronas (chamadas a modelos de IA de visão/áudio/texto sem bloquear), integridade relacional forte (child → chapter → node → evidence → state tem dependências claras e consultas que cruzam essas entidades — ex.: histórico de evidências por criança, nodes reestruturados por capítulo para métricas), e velocidade de iteração para MVP.

## Decisão
- **Python 3.12+** com **FastAPI** para a API.
- **PostgreSQL** como armazenamento principal, acessado via **Tortoise ORM** (async nativo, sem thread pool por baixo — se encaixa melhor no runtime assíncrono do FastAPI do que ORMs síncronos adaptados). Migrações com **Aerich** (ferramenta de migração oficial do Tortoise).
- Learning Nodes usam um campo `JSONField` para o conteúdo gerado por IA (`content_blocks`, `expected_keywords`) — flexibilidade onde o conteúdo é gerado dinamicamente, sem abrir mão de FK/integridade relacional nas entidades estruturais (child, chapter, node, evidence, state).
- Versionamento de Learning Node (`version_id`, `status: active/superseded`) é modelado como linhas imutáveis na própria tabela `learning_nodes` — nunca `update()` no conteúdo de uma versão existente, sempre `create()` de nova linha. Isso espelha o princípio "o papel é imutável" diretamente no nível de dado.
- **Pydantic v2** para todos os schemas de API/domínio (specs em `specs/` usam a mesma sintaxe propositalmente, para reduzir a distância entre spec e código). Tortoise models (`models.py`) ficam separados dos schemas Pydantic de API (`schemas.py`) — não expor o model do ORM diretamente na resposta HTTP; usar `tortoise.contrib.pydantic.pydantic_model_creator` ou schemas explícitos quando o contrato de API precisar divergir do model.
- **pytest + pytest-asyncio** como framework de testes:
  - Modo `asyncio_mode = "auto"` configurado em `pyproject.toml` (seção `[tool.pytest.ini_options]`) — elimina o decorator `@pytest.mark.asyncio` em cada test.
  - Testes unitários: Tortoise inicializado com `sqlite://:memory:` via fixture de sessão (`scope="function"`) — isolamento total, sem depender de Postgres real.
  - Testes de integração: usam o Postgres do `docker-compose.yml` (marcados com `@pytest.mark.integration`) — necessários para testar `JSONField`, queries com operadores JSON nativos do Postgres, e constraints que o SQLite não suporta.
  - `pytest-cov` para cobertura; mínimo aceitável definido por motor em `pyproject.toml` (`--cov-fail-under`).
  - Fixtures compartilhadas ficam em `tests/conftest.py`; fixtures específicas de motor ficam em `tests/<motor>/conftest.py`.
- **Lint e formatação via pre-commit** com quatro ferramentas em ordem fixa:
  1. **isort** — ordena imports (perfil `black` para compatibilidade).
  2. **black** — formatação de código; linha máxima de 88 caracteres.
  3. **flake8** — linting de estilo/erros; configurado para ignorar regras que conflitam com black (`E203`, `W503`) e respeitar o mesmo limite de linha.
  4. **mypy** — checagem de tipos estáticos; `strict = true` no `pyproject.toml`, com stubs instalados via `[tool.mypy]` por pacote externo quando necessário.
  - Executados via `pre-commit` (`.pre-commit-config.yaml` na raiz), garantindo que nenhum commit passa sem passar nas quatro etapas.
  - Na CI, rodar `pre-commit run --all-files` como step separado antes dos testes — falha rápido antes de executar a suíte completa.
- Blob storage (S3/GCS) para mídia (fotos, áudios) — Postgres guarda só a referência (`media_url`), nunca o binário.

## Consequências
- Cada motor (`app/engines/<nome>/`) é um pacote com `service.py` (lógica), `schemas.py` (Pydantic), `models.py` (Tortoise models), `router.py` (FastAPI).
- Toda mudança de schema passa por uma migração Aerich versionada (`aerich migrate` + `aerich upgrade`) — nunca alterar tabela manualmente em produção.
- Se o volume de eventos entre Evidence Engine → Learning State Engine crescer, pode ser necessário introduzir mensageria externa (ex.: fila) em vez de leitura direta de tabela — decisão adiada para uma ADR futura quando houver dado real de volume.

## Alternativas consideradas
- MongoDB: adequado à natureza semi-estruturada dos Learning Nodes, mas o domínio tem bastante relação estruturada entre entidades (child/chapter/node/evidence/state) e o produto precisa de consultas agregadas confiáveis para métricas (nodes reestruturados por capítulo, taxa de validação na primeira foto) — Postgres cobre a parte flexível (via `JSONField`) sem abrir mão de integridade relacional. Descartado.
- SQLAlchemy 2.0 (async) + Alembic: maduro e mais usado no ecossistema Python, mas seu modo async é uma camada sobre uma API historicamente síncrona, com mais boilerplate (sessão explícita, `async_sessionmaker`, etc.). Tortoise foi desenhado async desde a base e tem uma API mais próxima do Django ORM (menos fricção para escrever `service.py` de cada motor rapidamente). Descartado em favor de Tortoise por preferência do time.
