# AGENTS.md — Smart App

Este arquivo é o contrato de comportamento para **qualquer agente de IA** (Claude Code, Cursor, Aider, Amp, OpenHands, Codex CLI, etc.) que for gerar ou modificar código neste repositório. Leia isto por completo antes de tocar em qualquer arquivo.

Este projeto usa **Spec-Driven Development (SDD)**: nenhum código é escrito a partir de um prompt solto. Todo código nasce de uma spec em `specs/`, quebrada em tasks em `tasks/`, com critérios de aceitação verificáveis.

---

## 1. Contexto do produto (resumo — a fonte completa está em `specs/00-product-vision.md`)

Smart App é um app de pré-aprendizagem para crianças de 8–13 anos: a criança estuda o capítulo **antes** da aula, produzindo evidências físicas (mindmap escrito à mão + foto, explicação falada, resumo escrito à mão), que a IA valida e usa para adaptar o conteúdo.

A arquitetura conceitual tem **5 motores** (ver specs individuais):

1. **Ingestion Engine** — scanner, OCR, limpeza, segmentação, embeddings.
2. **Knowledge Engine** — transforma capítulo em Learning Nodes.
3. **Evidence Engine** — coleta evidências (foto, áudio, resumo, jogos, tempo).
4. **Learning State Engine** — estima confiança de aprendizagem por Learning Node.
5. **Generation Engine** — gera feedback, reestruturação, quiz, jogos — sob demanda.

## 2. Princípios de produto que são também restrições de engenharia

Estes não são "valores" abstratos — cada um vira regra de código. Nenhuma implementação pode violá-los:

| Princípio | Consequência técnica obrigatória |
|---|---|
| O papel é imutável | Reestruturação de conteúdo NUNCA deleta ou sobrescreve um Learning Node já validado. Sempre versiona (`version_id` incremental), nunca faz `UPDATE` destrutivo em evidência ou nó já validado. |
| Falso negativo é o pior erro | Validação de evidência tem *threshold* de aceitação generoso (~60-70% de match) e configurável por spec — nunca hardcoded como "exato". Em caso de dúvida do modelo, o default é validar, não rejeitar. |
| A culpa nunca é da criança | Toda mensagem de erro voltada ao usuário final atribui a causa a um problema técnico (ex: qualidade da foto), nunca ao desempenho da criança. Isso é requisito de copy, mas também de *design de API*: o backend deve retornar um `reason_code` neutro (`image_quality_low`, `not_recognized`), nunca algo como `answer_wrong`. |
| Reestruturação é cirúrgica | Regeneração de conteúdo opera sobre 1 Learning Node por vez, nunca sobre o capítulo inteiro. Qualquer função de reestruturação deve receber um `node_id`, nunca um `chapter_id` sozinho. |
| Idade calibra tudo | Todo prompt de geração de conteúdo recebe `profile.age` (ou faixa etária) como parâmetro obrigatório, nunca como opcional com default silencioso. |
| Geração em 2 camadas | Camada 1 (plano do capítulo) é gerada uma vez no onboarding. Camada 2 (quiz, jogos, avaliação de resumo) só é gerada sob demanda, no momento em que a criança chega lá — nunca antecipada. Isso é uma restrição de custo E de produto (evitar gerar sobre conteúdo que pode ser reestruturado). |

Se uma task pedir algo que conflita com esta tabela, o agente deve **parar e sinalizar o conflito**, não implementar mesmo assim.

## 3. Stack (ver `adr/0002-stack-choice.md` para o racional)

- Python 3.12+
- FastAPI (API), Pydantic v2 (validação/schemas)
- PostgreSQL via Tortoise ORM (async nativo) + asyncpg, migrações com Aerich — entidades estruturais (child, chapter, node, evidence, state) são tabelas relacionais com FK entre si; campos de conteúdo gerado por IA (`content_blocks`, `expected_keywords`) usam `JSONField`
- Versionamento de Learning Node é feito por `create()` de nova linha (nunca `update()` de conteúdo já existente) — é assim que "o papel é imutável" se traduz em nível de banco
- pytest + pytest-asyncio, com Tortoise apontando para `sqlite://:memory:` em testes unitários (sem depender de Postgres real); testes de integração usam o Postgres do `docker-compose.yml`
- Estrutura de diretórios: um pacote por módulo em `app/modules/<modulo>/`, seguindo o padrão BoilerplateV2:
  - `models/<entidade>.py` — Tortoise ORM models
  - `dtos.py` — schemas Pydantic (Create/Get DTOs)
  - `repositories/<entidade>_repository.py` — acesso a dados (herda de `common/abstracts/repository.py`)
  - `use_cases/<acao>_<entidade>.py` — uma classe por operação de negócio
  - `api/v1/routes.py` — FastAPI router (prefixo `/api/v1/<recurso>`)
- DI via `app/core/dependencies.py` (`DependencyInjectionContainer`) — container injetado nas rotas via `Depends(container.<use_case>)`
- Resposta padrão: `Response[T]` genérico em `app/modules/common/dtos/response.py`
- Erros de negócio: `UseCaseException` em `app/modules/common/exceptions/use_case_exception.py` — nunca HTTP exceptions direto nos use cases
- Rotas registradas centralmente em `app/core/routers.py`; settings em `app/config/settings.py`

Não trocar de stack silenciosamente. Se uma spec exigir algo que o stack atual não suporta bem, abrir uma ADR nova propondo a mudança — não decidir sozinho.

## 4. Workflow obrigatório para qualquer mudança

1. **Ler a spec relevante** em `specs/`. Se a spec não existe ou está incompleta para o que foi pedido, escrever/completar a spec primeiro (usando `specs/_template.md`), não pular direto para código.
2. **Quebrar em uma ou mais tasks** em `tasks/`, usando `tasks/_template.md`. Cada task deve ser implementável e testável isoladamente.
3. **Implementar** apenas o necessário para a task, seguindo a spec.
4. **Escrever testes que verifiquem os critérios de aceitação da spec**, não apenas "roda sem erro".
5. **Rodar a suíte de testes completa** antes de considerar a task concluída.
6. **Atualizar o status da task e, se necessário, da spec** (`Status: rascunho / em implementação / implementado / validado em produção`).

Nunca gerar código de um motor inteiro de uma vez a partir da visão geral — sempre via spec → task.

## 5. Definition of Done de uma task

- [ ] Código implementado conforme a spec referenciada
- [ ] Testes cobrindo os critérios de aceitação da spec (não só happy path)
- [ ] Nenhuma violação da tabela da seção 2
- [ ] `pytest` passando localmente
- [ ] Docstring/comentário curto explicando decisões não óbvias
- [ ] Task marcada como concluída em `tasks/`

## 6. Como rodar o projeto localmente

```bash
docker compose up -d          # sobe PostgreSQL local
pip install -e ".[dev]"
aerich upgrade                 # aplica migrações
uvicorn app.main:app --reload
pytest
```

## 7. O que o agente NÃO deve fazer

- Não inventar requisitos que não estão em nenhuma spec — perguntar ou registrar em "Perguntas em aberto" na spec.
- Não implementar a visão do responsável (fora do MVP — ver `specs/00-product-vision.md`, seção Fora do escopo).
- Não commitar chaves de API ou segredos — usar `.env` (ver `.env.example`).
- Não remover o campo `reason_code` neutro dos erros de validação, mesmo que pareça "código morto".
