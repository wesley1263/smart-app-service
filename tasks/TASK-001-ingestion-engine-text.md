# TASK-001 — Ingestion Engine (caminho texto)

**Spec:** `specs/01-ingestion-engine.md` (R3, R4, R5, R7)
**Status:** concluída
**Complexidade estimada:** M
**Depende de:** nenhuma

## Descrição
Implementar o Ingestion Engine para o caminho de texto colado diretamente (R3), com limpeza básica e segmentação por parágrafo (R4, R5) e persistência de `school_start_date` (R7). Expõe `POST /chapters` e `GET /chapters/{chapter_id}`. Tipos `image` e `link` são aceitos no payload mas retornam `status: failed` com reason_code `not_implemented` (dependem de decisão de OCR ainda em aberto — spec 01, seção 9).

## Critérios de aceitação
- [x] `POST /chapters` com tipo `text` retorna `chapter_id` e `status: ready` com segmentos não-vazios.
- [x] `GET /chapters/{chapter_id}` retorna status e segmentos quando `ready`.
- [x] `school_start_date` persiste e é recuperável via GET.
- [x] `POST /chapters` com tipo `image` ou `link` retorna 200 com `status: failed` e `reason_code: not_implemented`.
- [x] Todos os critérios da spec 01, seção 8, cobertos por testes.

## Notas de implementação
- Segmentação: split em `\n\n`, strip de cada parte, filtrar vazios. Mínimo 1 segmento.
- OCR e scraping: stubs retornam `failed`/`not_implemented` até decisão da spec 01 seção 9.
- Tortoise model `IngestedChapter` usa `UUIDField` como PK e `JSONField` para `segments`.
- `generate_schemas=True` detectado automaticamente quando `DATABASE_URL` começa com `sqlite` — testes em memória funcionam sem Aerich; produção usa Aerich normalmente.
- `StrEnum` para status e tipos (Python 3.11+), elimina strings literais soltas.
- Tipos `image`/`link` aceitam o payload e retornam `failed`/`not_implemented` (sem 501) para manter contrato de API estável enquanto decisão de OCR está em aberto.
