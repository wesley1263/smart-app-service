# SPEC-02 — Knowledge Engine

**Status:** rascunho
**Depende de:** `01-ingestion-engine.md`

## 1. Contexto
Transforma o capítulo ingerido em Learning Nodes: as unidades atômicas de conhecimento que o resto do sistema (evidência, estado, geração) manipula.

## 2. Objetivo
A partir de um `IngestedChapter`, produzir a Camada 1 completa: Learning Nodes (Pareto 80/20), mindmap esperado por nó, e um plano de sessões distribuído respeitando `school_start_date`.

## 3. Não-objetivo
Não gera quiz, jogos ou avaliação de resumo (Camada 2 — Generation Engine). Não decide reestruturação (Learning State Engine).

## 4. Requisitos funcionais
R1. Selecionar, dos segmentos ingeridos, os que carregam ~80% do valor pedagógico do capítulo (Pareto), descartando ou de-priorizando o resto.
R2. Quebrar o conteúdo selecionado em Learning Nodes pequenos (carga cognitiva baixa por nó — Sweller).
R3. Para cada Learning Node, gerar `expected_keywords` (estrutura do mindmap esperado).
R4. Toda geração de texto de um node deve ser parametrizada pela linguagem do tema escolhido pela criança (Minecraft, mangá, DC, Marvel) e pela idade do perfil — ambos obrigatórios, nunca default silencioso.
R5. Gerar um plano de sessões (6–8 sessões de 20–30 min por capítulo típico) distribuído no calendário, terminando antes de `school_start_date`.
R6. Cada Learning Node tem um `version_id` inicial = 1. Reestruturação futura (spec `05`) incrementa a versão, nunca sobrescreve.

## 5. Requisitos não funcionais
Geração de Camada 1 é uma operação cara (uma vez por capítulo) — deve ser assíncrona com status consultável, não bloquear a UI.

## 6. Modelo de dados
```python
class LearningNode(BaseModel):
    id: str
    chapter_id: str
    version_id: int = 1
    concept: str
    expected_keywords: list[str]
    content_blocks: list[str]  # já na linguagem do tema
    order: int
    status: Literal["active", "superseded"]

class SessionPlanItem(BaseModel):
    session_number: int
    node_ids: list[str]
    scheduled_date: date
```

## 7. Contrato de API
`POST /chapters/{chapter_id}/plan` — dispara geração da Camada 1 (assíncrono).
`GET /chapters/{chapter_id}/nodes` — lista Learning Nodes ativos.
`GET /chapters/{chapter_id}/sessions` — retorna o plano de sessões.

## 8. Critérios de aceitação (testáveis)
- **Dado** um capítulo ingerido e um `school_start_date` em 14 dias, **quando** o plano é gerado, **então** todas as `scheduled_date` são anteriores a `school_start_date`.
- **Dado** um perfil de 8 anos e outro de 13 anos para o mesmo capítulo, **quando** os nodes são gerados, **então** o texto de `content_blocks` difere em densidade/linguagem entre os dois.
- **Dado** um node gerado, **quando** inspecionado, **então** `version_id == 1` e `status == "active"`.

## 9. Perguntas em aberto
- Como medir "80% do valor pedagógico" de forma programática — heurística inicial vs modelo dedicado.
- Número mínimo/máximo de `expected_keywords` por node — calibrar com o teste de risco de leitura de manuscrito.
