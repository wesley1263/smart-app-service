# Smart App — AI Development Harness

Este repositório é um **harness de desenvolvimento orientado a spec (SDD)** para o Smart App. Ele existe para que qualquer agente de IA (Claude Code, Cursor, Aider, Amp, OpenHands, Codex CLI...) — ou você mesmo — trabalhe a partir de especificações verificáveis, não de prompts soltos.

## Comece por aqui

1. **Leia `AGENTS.md`** — é o contrato de comportamento para qualquer agente neste repo. Se você for usar um agente de IA para codar, aponte-o para este arquivo primeiro (a maioria das ferramentas — Claude Code, Cursor, Aider — já lê `AGENTS.md`/`CLAUDE.md` automaticamente na raiz).
2. **`specs/`** — uma spec por motor da arquitetura (Ingestion, Knowledge, Evidence, Learning State, Generation), mais `00-product-vision.md` com a visão consolidada. `03-evidence-engine.md` está mais detalhada e serve de modelo de qualidade para as próximas.
3. **`tasks/`** — unidades de trabalho pequenas, derivadas das specs, com critérios de aceitação testáveis. `TASK-000` é a primeira: validar a leitura de manuscrito infantil antes de qualquer código de produto (é o maior risco do projeto, ver `specs/00-product-vision.md`).
4. **`adr/`** — decisões de arquitetura registradas. `0002-stack-choice.md` define Python/FastAPI/PostgreSQL (Tortoise ORM + Aerich).
5. **`app/`** — scaffold do backend, vazio de propósito: pastas por motor (`app/engines/<nome>/service.py|schemas.py|router.py`), prontas para receber implementação task por task.

## Fluxo de trabalho (resumo — detalhado em AGENTS.md)

```
specs/00-product-vision.md
        │
        ▼
specs/0X-<motor>.md  (contrato: requisitos + modelo de dados + API + critérios de aceitação)
        │
        ▼
tasks/TASK-NNN-<nome>.md  (unidade pequena, testável)
        │
        ▼
implementação em app/engines/<motor>/  +  teste em tests/
        │
        ▼
pytest verde  →  task concluída  →  status atualizado
```

## Rodando localmente

```bash
cp .env.example .env
docker compose up -d          # sobe PostgreSQL local
pip install -e ".[dev]"
aerich upgrade                 # aplica migrações (aerich init-db na primeira vez)
uvicorn app.main:app --reload
pytest
```

## Como pedir a um agente para trabalhar aqui

Exemplo de prompt (não solto — referenciando a spec/task):

> "Implemente a TASK-000 (`tasks/TASK-000-teste-risco-manuscrito.md`). Leia `AGENTS.md` e `specs/03-evidence-engine.md` antes de começar."

Evite pedir "implementa o Evidence Engine inteiro" — o harness existe justamente para forçar a quebra em specs → tasks pequenas e verificáveis.

## Próximo passo recomendado

Rodar `TASK-000` primeiro (fora do código de produto) para validar o maior risco do projeto antes de escrever qualquer linha de `app/`.
