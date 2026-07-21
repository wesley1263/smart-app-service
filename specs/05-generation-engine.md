# SPEC-05 — Generation Engine

**Status:** rascunho
**Depende de:** `02-knowledge-engine.md`, `04-learning-state-engine.md`

## 1. Contexto
Motor de geração sob demanda (Camada 2): feedback de validação, reestruturação cirúrgica de node, quiz de repetição espaçada, jogos e avaliação de resumo. Só gera quando a criança efetivamente chega naquele ponto do fluxo — nunca antecipadamente.

## 2. Objetivo
Gerar, sob demanda e no tom do tema/idade, os artefatos de Camada 2, respeitando a restrição de reestruturação cirúrgica (nunca o capítulo inteiro).

## 3. Não-objetivo
Não decide QUANDO reestruturar (isso é sinalizado pelo Learning State Engine). Não coleta evidência (Evidence Engine).

## 4. Requisitos funcionais
R1. Reestruturação: dado um `node_id` marcado `needs_restructure`, gerar uma nova versão do node (quebrado em pedaços menores, linguagem mais simples), incrementando `version_id`. O node anterior é marcado `status: superseded`, nunca deletado.
R2. Quiz: gerado ao final do estudo de uma sessão, focado nos nodes com `confidence_estimate` mais baixa daquela sessão.
R3. Jogo (MVP: forca): gerado a partir das `expected_keywords` já validadas na sessão — nunca de conteúdo não validado.
R4. Avaliação de resumo: recebe o resumo escrito (via evidência de foto) e retorna feedback construtivo estruturado (o que ficou bom / o que faltou), no tom do tema.
R5. Repetição espaçada: agendar reaparecimento do quiz/jogo de cada node em intervalos crescentes, idealmente sincronizados com a véspera da aula correspondente (`school_start_date` do capítulo / data estimada do bloco).
R6. Toda geração de texto voltada à criança passa pelo parâmetro de tema + idade (mesma regra da spec 02, R4).

## 5. Requisitos não funcionais
Latência de geração deve ser escondida em momentos naturais do fluxo (Pomodoro, escrita do resumo) — gerar em background assim que o gatilho ocorre, não só quando a criança chega na tela seguinte.

## 6. Modelo de dados
```python
class RestructureResult(BaseModel):
    original_node_id: str
    new_node: "LearningNode"  # ver spec 02
    reason: str  # interno, não exposto à criança

class QuizItem(BaseModel):
    node_id: str
    question: str
    options: list[str]
    correct_index: int

class GameHangman(BaseModel):
    node_id: str
    keyword: str
    theme_context: str

class SummaryFeedback(BaseModel):
    child_id: str
    node_id: str
    strengths: list[str]
    gaps: list[str]
    tone_theme: str
```

## 7. Contrato de API
`POST /nodes/{node_id}/restructure` — interno, disparado pelo sinal do Learning State Engine.
`POST /sessions/{session_id}/quiz` — gera quiz sob demanda.
`POST /sessions/{session_id}/game` — gera jogo (forca no MVP).
`POST /nodes/{node_id}/summary-feedback` — avalia resumo enviado.

## 8. Critérios de aceitação (testáveis)
- **Dado** um node `needs_restructure`, **quando** reestruturado, **então** existe um novo node com `version_id` incrementado e o antigo passa a `status: superseded`, mas ainda é recuperável (não deletado).
- **Dado** uma sessão com 3 nodes validados e 1 com confiança baixa, **quando** o quiz é gerado, **então** o item sobre o node de confiança baixa aparece (priorização).
- **Dado** um jogo de forca gerado, **quando** inspecionado, **então** a `keyword` pertence às `expected_keywords` de um node já `validated` naquela sessão (nunca de node não validado).
- **Dado** dois perfis (8 e 13 anos) recebendo `SummaryFeedback` para o mesmo node, **quando** comparados, **então** o tom/linguagem difere.

## 9. Perguntas em aberto
- Intervalo exato da repetição espaçada (curva de esquecimento aplicada) — parametrizar, não hardcode.
- Onde fica o limite entre "reestruturação" e "novo node do zero" quando o conteúdo original é irrecuperável.
