# SPEC-01 — Ingestion Engine

**Status:** rascunho
**Depende de:** —

## 1. Contexto
Ponto de entrada do sistema: transforma o material escolar (foto, link ou texto de um capítulo) em conteúdo limpo e estruturado, pronto para o Knowledge Engine.

## 2. Objetivo
Receber uma entrada bruta (imagem, link, texto colado) e produzir um documento limpo, segmentado e indexado (embeddings), associado a um `chapter_id`.

## 3. Não-objetivo
Não decide o que é pedagogicamente relevante (isso é o Knowledge Engine). Não interage com a criança.

## 4. Requisitos funcionais
R1. Aceitar upload de imagem(ns) do material e rodar OCR.
R2. Aceitar link e fazer scraping de texto (com fallback gracioso se falhar).
R3. Aceitar texto colado diretamente.
R4. Limpar ruído (cabeçalhos repetidos, numeração de página, etc.).
R5. Segmentar o documento em unidades coerentes (parágrafos/seções) preservando ordem.
R6. Gerar embeddings por segmento e indexar para uso posterior pelo Knowledge Engine.
R7. Capturar a data informada de início do conteúdo na escola (`school_start_date`) e associá-la ao `chapter_id` — insumo do motor de ritmo (sessões).

## 5. Requisitos não funcionais
Deve tolerar fotos de baixa qualidade (celular, luz ruim) sem quebrar — degradar graciosamente, nunca falhar silenciosamente.

## 6. Modelo de dados
```python
class RawSource(BaseModel):
    id: str
    chapter_id: str
    type: Literal["image", "link", "text"]
    raw_ref: str  # URL do blob ou o texto em si

class IngestedChapter(BaseModel):
    chapter_id: str
    child_id: str
    subject: str
    school_start_date: date
    segments: list[str]
    status: Literal["processing", "ready", "failed"]
```

## 7. Contrato de API
`POST /chapters` — cria capítulo a partir de uma ou mais `RawSource`, retorna `chapter_id` com status `processing`.
`GET /chapters/{chapter_id}` — retorna status e, se `ready`, os segmentos.

## 8. Critérios de aceitação (testáveis)
- **Dado** uma imagem legível de um capítulo, **quando** processada, **então** `status == "ready"` e `segments` não está vazio.
- **Dado** uma imagem ilegível, **quando** processada, **então** `status == "failed"` com motivo explícito (nunca trava em `processing`).
- **Dado** um `school_start_date` informado, **quando** o capítulo é criado, **então** ele é persistido e recuperável via GET.

## 9. Perguntas em aberto
- Motor de OCR: serviço externo (Vision API) vs modelo próprio — depende do teste de risco de leitura de manuscrito, mas aqui é OCR de material impresso/apostila, caso diferente.
- Estratégia de chunking para embeddings (tamanho de segmento) — definir ao implementar.
