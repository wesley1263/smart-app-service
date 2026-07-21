# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Contrato completo de comportamento de agentes (princípios de produto, SDD, restrições) está em `AGENTS.md`. Este arquivo foca nos comandos práticos e na arquitetura técnica.

---

## Protocolo de trabalho (seguir sempre)

1. **Analisar** — ler o código atual relevante antes de propor qualquer mudança.
2. **Spec → Task** — toda mudança não trivial exige spec em `specs/` e task em `tasks/`. Se a spec está incompleta, completá-la primeiro usando `specs/_template.md`; tasks usam `tasks/_template.md`.
3. **Branch** — criar branch com prefixo adequado (`feat/`, `fix/`, `bugfix/`, `hotfix/`, `refact/`, `test/`). Nunca commitar sem pedido explícito.
4. **Red → Green** — escrever o teste (que vai falhar) antes do código mínimo para ele passar.
5. **Lint** — rodar `docker compose run --rm lint` e corrigir tudo antes de considerar a task concluída.
6. **Changelog** — atualizar `CHANGELOG.md` ao final (formato Keep a Changelog).

**Regra absoluta:** toda execução de comandos usa Docker Compose, nunca o host local. Testes rodam com `docker compose run --rm test`.

---

## Comandos

```bash
# Ambiente
docker compose up -d              # sobe PostgreSQL local (porta 5432)
pip install -e ".[dev]"           # instala dependências incluindo dev

# Desenvolvimento
aerich upgrade                    # aplica migrações pendentes
uvicorn app.main:app --reload     # inicia a API em http://localhost:8000

# Testes
docker compose run --rm test      # suíte completa
pytest tests/path/test_file.py::test_name   # teste único (host — só durante ciclo red/green)
pytest -k "nome_parcial"          # filtrar por nome

# Lint (pre-commit: isort → black → flake8 → mypy)
docker compose run --rm lint      # roda todos os checks
pre-commit run --all-files        # equivalente fora do Docker
```

---

## Arquitetura

### Estrutura de módulos — `app/modules/<modulo>/`

Cada módulo segue o padrão BoilerplateV2 adaptado para Tortoise:

```
app/modules/<modulo>/
├── models/<entidade>.py          # Tortoise ORM — registrar em app/core/db.py::MODEL_MODULES
├── dtos.py                       # Pydantic v2 (CreateXxxDto, GetXxxDto)
├── repositories/<entidade>_repository.py   # herda de common/abstracts/repository.py
├── use_cases/<acao>_<entidade>.py          # uma classe por operação, método execute()
└── api/v1/routes.py              # FastAPI router — registrar em app/core/routers.py
```

Módulos: `ingestion` → `knowledge` → `evidence` → `learning_state` → `generation`.

### DI Container — `app/core/dependencies.py`

`DependencyInjectionContainer` é o único lugar que instancia repositórios e use cases. Rotas injetam via `Depends(container.<use_case>)`.

```python
# Padrão de injeção nas rotas
use_case: Annotated[CreateChapterUseCase, Depends(container.create_chapter)]
```

### Resposta padrão e erros

- Toda rota retorna `Response[T]` de `app/modules/common/dtos/response.py`.
- Erros de negócio: lançar `UseCaseException(message, status_code)` nos use cases; a rota converte para `HTTPException`.

### Registro de models e routers

- **Novo model**: adicionar `"app.modules.<modulo>.models.<entidade>"` em `app/core/db.py::MODEL_MODULES`.
- **Novo router**: importar e registrar em `app/core/routers.py::include_routers`.
- `generate_schemas` é `True` automaticamente quando `DATABASE_URL` começa com `sqlite` (testes); em produção o Aerich gerencia.

### Banco de dados

- Entidades estruturais (child, chapter, node, evidence, state): tabelas relacionais com FK.
- Conteúdo gerado por IA (`content_blocks`, `expected_keywords`): `JSONField` dentro da entidade.
- Versionamento de Learning Node: sempre `create()` de nova linha com `version_id` incremental — nunca `update()` de linha existente.

### Testes

`tests/conftest.py` define `DATABASE_URL=sqlite://:memory:` via `os.environ.setdefault` **antes** de qualquer import de `app.*`.

Padrão obrigatório:
```python
with TestClient(app) as client:   # dispara startup/shutdown do FastAPI (Tortoise init)
    ...
```

### Configuração

`app/config/settings.py` — `Settings` via `pydantic-settings` com `lru_cache`. Variáveis em `.env` (ver `.env.example`).

---

## Restrições de engenharia (resumo — detalhes em `AGENTS.md` seção 2)

| Regra | O que nunca fazer |
|---|---|
| Imutabilidade | `UPDATE` em evidence ou Learning Node já validado |
| Threshold generoso | Hardcodar threshold de validação como "exato" |
| `reason_code` neutro | Retornar `answer_wrong` ou qualquer código que culpe a criança |
| Reestruturação cirúrgica | Passar `chapter_id` sozinho para função de regeneração |
| `profile.age` obrigatório | Omitir idade com default silencioso em prompt de geração |
| Geração sob demanda | Gerar Camada 2 (quiz/jogos) antecipadamente no onboarding |