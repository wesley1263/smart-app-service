# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Contrato completo de comportamento de agentes (princípios de produto, SDD, restrições) está em `AGENTS.md`. Este arquivo foca nos comandos práticos e na arquitetura técnica.

---

## Protocolo de trabalho (seguir sempre)

1. **Analisar** — ler o código atual relevante antes de propor qualquer mudança.
2. **Branch** — criar branch com prefixo adequado (`feat/`, `fix/`, `bugfix/`, `hotfix/`, `refact/`, `test/`). Nunca commitar sem pedido explícito.
3. **Red → Green** — escrever o teste (que vai falhar) antes do código mínimo para ele passar.
4. **Lint** — rodar `docker compose run --rm lint` e corrigir tudo antes de considerar a task concluída.
5. **Changelog** — atualizar `CHANGELOG.md` ao final (formato Keep a Changelog).

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

### 5 motores em `app/engines/<motor>/`

Cada motor é um pacote independente com quatro arquivos fixos:

| Arquivo | Responsabilidade |
|---|---|
| `models.py` | Tortoise ORM models — nunca expor direto na resposta HTTP |
| `schemas.py` | Pydantic v2 — contratos de entrada/saída da API |
| `service.py` | Lógica de domínio — chamado pelo router, nunca pelo ORM diretamente |
| `router.py` | FastAPI — registrado em `app/main.py` conforme a spec é implementada |

Motores: `ingestion` → `knowledge` → `evidence` → `learning_state` → `generation` (fluxo de dados).

### Registro de models e routers

- **Novo model**: adicionar o módulo em `app/core/db.py::MODEL_MODULES` para o Aerich enxergar.
- **Novo router**: registrar em `app/main.py` com `app.include_router(...)`.
- Schema nunca é auto-gerado em runtime (`generate_schemas=False` em `main.py`) — sempre via `aerich migrate && aerich upgrade`.

### Banco de dados

- Entidades estruturais (child, chapter, node, evidence, state): tabelas relacionais com FK.
- Conteúdo gerado por IA (`content_blocks`, `expected_keywords`): `JSONField` dentro da entidade.
- Versionamento de Learning Node: sempre `create()` de nova linha com `version_id` incremental — nunca `update()` de linha existente.

### Testes

`tests/conftest.py` define `DATABASE_URL=sqlite://:memory:` via `os.environ.setdefault` **antes** de qualquer import de `app.*`. Isso é obrigatório para que os testes unitários não dependam do Postgres.

Padrão obrigatório nos testes que sobem a app:
```python
with TestClient(app) as client:   # correto — dispara startup/shutdown do FastAPI
    ...
# TestClient(app) solto sem context manager → Tortoise não inicializa
```

Testes de integração (que precisam de `JSONField` ou operadores JSON nativos do Postgres) são marcados com `@pytest.mark.integration` e usam o Postgres do `docker-compose.yml`.

### Configuração

`app/core/config.py` usa `pydantic-settings` com `lru_cache`. Variáveis em `.env` (ver `.env.example`). As duas únicas variáveis hoje são `ENVIRONMENT` e `DATABASE_URL`.

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