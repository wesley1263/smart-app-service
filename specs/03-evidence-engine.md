# SPEC-03 — Evidence Engine

**Status:** rascunho
**Depende de:** `02-knowledge-engine.md` (Learning Nodes precisam existir antes de haver evidência sobre eles)

## 1. Contexto

O Evidence Engine é o coração do produto: é o que diferencia o Smart App de "mais um app com quiz e troféu". Ele coleta e valida trabalho físico (foto de mindmap/resumo) e entendimento falado (áudio, técnica de Feynman), e produz o sinal que alimenta o Learning State Engine.

## 2. Objetivo

Receber uma evidência (foto ou áudio) associada a um Learning Node, validá-la com tolerância generosa, nunca culpar a criança pela falha, e emitir um resultado estruturado que o Learning State Engine consegue consumir.

## 3. Não-objetivo

- Não decide se o conteúdo deve ser reestruturado (isso é o Learning State Engine + Generation Engine).
- Não gera os jogos ou quiz (isso é o Generation Engine).
- Não faz correção ortográfica ou avaliação de "qualidade de redação" — só entendimento do conceito.

## 4. Requisitos funcionais

R1. Aceitar evidência do tipo `photo` (mindmap incremental ou resumo) associada a `node_id` + `child_id` + `session_id`.
R2. Aceitar evidência do tipo `audio` (explicação falada) associada a `node_id` + `child_id`.
R3. Validação de foto: comparar o conteúdo capturado com as `expected_keywords` do Learning Node. Match ≥ ~60–70% → `status: validated`. Abaixo disso → `status: needs_retry`, nunca `status: failed`/`rejected` atribuído à criança.
R4. Toda resposta de `needs_retry` deve conter um `reason_code` neutro (ex: `image_quality_low`, `handwriting_unclear`, `insufficient_content`) e uma mensagem de retry gerada no tom do tema escolhido, atribuindo a causa à foto, nunca à criança.
R5. Validação de áudio: transcrever e avaliar se a explicação (Feynman) é coerente com o conceito do node. Retornar `understanding_estimate` (0–100) e, se aplicável, `misconceptions: []` identificados.
R6. Toda evidência validada é armazenada de forma imutável — nunca é sobrescrita; nova tentativa gera novo registro (`attempt_number` incremental), o histórico completo é preservado.
R7. Emitir um evento/registro de "evidência processada" que o Learning State Engine consome (fila interna ou callback — decisão de infraestrutura em ADR).

## 5. Requisitos não funcionais

- Latência percebida: validação de foto deve responder em tempo compatível com a criança esperando na tela (idealmente <5s; acima disso, feedback de loading no tom do tema).
- Custo de geração de IA: usar modelo de visão mais barato disponível que atinja a taxa de acerto validada no teste de risco (spec `00`, seção 8).
- Dados sensíveis: fotos/áudios de crianças. Retenção e acesso devem seguir política de privacidade a definir (fora do escopo desta spec, mas o schema já deve prever `retention_policy` como campo, não hardcoded).

## 6. Modelo de dados

```python
class Evidence(BaseModel):
    id: str
    child_id: str
    node_id: str
    session_id: str
    type: Literal["photo_mindmap", "photo_summary", "audio_explanation"]
    attempt_number: int
    media_url: str  # referência a blob storage, nunca o binário direto
    created_at: datetime

class EvidenceValidationResult(BaseModel):
    evidence_id: str
    status: Literal["validated", "needs_retry"]
    match_score: float | None       # para foto
    understanding_estimate: float | None  # para áudio, 0-100
    reason_code: str | None         # obrigatório se needs_retry
    feedback_message: str           # gerado no tom do tema, nunca técnico
    misconceptions: list[str] = []
```

## 7. Contrato de API

`POST /children/{child_id}/nodes/{node_id}/evidence`
- Request: `{ type, session_id, media_url, attempt_number }`
- Response 200: `EvidenceValidationResult`
- Response 422: erro de validação de payload (não confundir com `needs_retry`, que é 200 — a validação de conteúdo nunca é um erro HTTP)

`GET /children/{child_id}/nodes/{node_id}/evidence`
- Retorna histórico completo de tentativas (imutável, nunca deletado)

## 8. Critérios de aceitação (testáveis)

- **Dado** uma foto com match_score de 65%, **quando** validada, **então** `status == "validated"`.
- **Dado** uma foto com match_score de 40%, **quando** validada, **então** `status == "needs_retry"` e `reason_code` está preenchido e não é `None`.
- **Dado** uma evidência `needs_retry`, **quando** a resposta é inspecionada, **então** `feedback_message` não contém nenhuma referência a desempenho da criança (validado por lista de termos proibidos: "errado", "não sabia", "tente entender melhor").
- **Dado** duas tentativas para o mesmo `node_id`, **quando** a segunda é enviada, **então** a primeira evidência continua acessível via `GET` (imutabilidade).
- **Dado** um áudio com `understanding_estimate` de 25 após a 2ª tentativa no mesmo node, **quando** processado, **então** o resultado é sinalizado para o Learning State Engine como candidato a reestruturação (não é o Evidence Engine que decide reestruturar, apenas sinaliza).

## 9. Perguntas em aberto

- Qual modelo/API de visão será usado para leitura de manuscrito? Depende do resultado do teste de risco (spec `00`).
- O `match_score` é calculado via embeddings semânticos das `expected_keywords` ou via OCR + comparação textual direta? Precisa decisão técnica antes da implementação de R3.
- Fila interna (ex: leitura direta da tabela `evidence_validation_results` pelo Learning State Engine, em memória) vs mensageria externa para o evento de R7 — decidir em ADR quando o volume esperado for conhecido.
