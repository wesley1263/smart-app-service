# SPEC-04 — Learning State Engine

**Status:** rascunho
**Depende de:** `02-knowledge-engine.md`, `03-evidence-engine.md`

## 1. Contexto
Consome os resultados do Evidence Engine e mantém, por criança e por Learning Node, uma estimativa de confiança de aprendizagem. É essa estimativa que decide se um node precisa de reestruturação.

## 2. Objetivo
Manter um estado atualizado (`confidence_estimate`) por `(child_id, node_id)`, agregando múltiplas evidências, e sinalizar ao Generation Engine quando um node cruza o limiar de reestruturação.

## 3. Não-objetivo
Não gera o conteúdo reestruturado (Generation Engine). Não decide o tom do feedback (Evidence Engine).

## 4. Requisitos funcionais
R1. Atualizar `confidence_estimate` (0–100) a cada nova `EvidenceValidationResult` recebida, usando uma agregação que dá mais peso a evidências recentes.
R2. Após **2 ou mais** validações abaixo de ~20–30% de confiança no mesmo node, marcar o node como `needs_restructure = true` e emitir sinal para o Generation Engine.
R3. Reestruturação nunca é retroativa: o estado de nodes já validados (`status: active`, confiança alta) nunca é reaberto por causa de um node diferente.
R4. Manter histórico de evolução do estado (não só o valor atual) — necessário para métricas de sucesso (nodes reestruturados por capítulo) e, futuramente, para a visão do responsável.

## 5. Requisitos não funcionais
Cálculo de estado deve ser barato (sem chamada a LLM) — é agregação determinística sobre os resultados que o Evidence Engine já produziu.

## 6. Modelo de dados
```python
class LearningState(BaseModel):
    child_id: str
    node_id: str
    confidence_estimate: float
    evidence_count: int
    needs_restructure: bool
    history: list[tuple[datetime, float]]
```

## 7. Contrato de API
`GET /children/{child_id}/nodes/{node_id}/state` — estado atual.
Consumido internamente via evento do Evidence Engine (R7 da spec 03) — sem endpoint de escrita direta exposto ao cliente.

## 8. Critérios de aceitação (testáveis)
- **Dado** duas evidências consecutivas com `understanding_estimate` de 20 e 25, **quando** processadas, **então** `needs_restructure == True`.
- **Dado** uma evidência com confiança alta seguida de uma baixa, **quando** processadas, **então** o node NÃO é marcado para reestruturação após só 1 evidência baixa (requer 2+).
- **Dado** o node A marcado para reestruturação, **quando** consultado o estado do node B (não relacionado), **então** o estado de B é inalterado.

## 9. Perguntas em aberto
- Fórmula exata de agregação (média ponderada simples vs decaimento exponencial) — decidir com dados reais de teste.
