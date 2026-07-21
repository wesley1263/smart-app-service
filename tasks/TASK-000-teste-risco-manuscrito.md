# TASK-000 — Validar taxa de acerto de leitura de manuscrito infantil

**Spec:** `specs/00-product-vision.md` (seção 5, "Pré-requisito antes de qualquer código de produto") e `specs/03-evidence-engine.md` (R3, Perguntas em aberto)
**Status:** em andamento — script implementado, aguarda execução com fotos reais
**Complexidade estimada:** P
**Depende de:** nenhuma — é a TASK-000 de propósito, deve rodar antes de qualquer outra.

## Descrição

Este NÃO é um endpoint de produção. É um script isolado (`scripts/handwriting_risk_test.py`) que:

1. Recebe um diretório com 10–15 fotos reais de mindmaps/resumos escritos à mão por crianças de 8–13 anos.
2. Para cada foto, chama o modelo de visão candidato com um prompt de validação equivalente ao que o Evidence Engine usará em produção (comparação com uma lista de `expected_keywords` fornecida manualmente por foto, em um CSV/JSON de gabarito).
3. Calcula a taxa de acerto (match ≥ 60–70% conforme spec 03, R3) e imprime um relatório simples: taxa de acerto geral, e quais fotos falharam.

Este script existe para decidir, com dados reais, se o modelo de visão escolhido é viável **antes** de qualquer linha de código de produto ser escrita. Se a taxa de acerto for baixa, a spec 03 precisa ser revisitada (mudar de modelo, mudar o threshold, ou repensar a modalidade de validação) antes de prosseguir.

## Critérios de aceitação

- [x] Script roda localmente com `python scripts/handwriting_risk_test.py --input <dir> --gabarito <arquivo>`.
- [x] Relatório final mostra taxa de acerto agregada e lista de fotos abaixo do threshold com o motivo (se disponível na resposta do modelo).
- [x] Não depende de nenhum código de `app/` — é standalone, para não acoplar a decisão de produto a infraestrutura ainda não construída.
- [ ] Resultado documentado em `specs/03-evidence-engine.md`, seção 9 — **pendente: executar com fotos reais e registrar decisão**.

## Notas de implementação

- Script agnóstico de provider via LiteLLM. Modelo default: `gemini/gemini-2.0-flash`.
- Gabarito: JSON com `{ "foto.jpg": { "node": "...", "expected_keywords": [...] } }`. Ver `scripts/gabarito_example.json`.
- Match é case-insensitive; sinônimos contam se o modelo os mapear para o keyword original.
- `--output resultado.json` salva relatório completo para análise posterior.
- API key lida do ambiente conforme provider: `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (ver `.env.example`).
- Pausa de 0.5s entre fotos para evitar rate limit.
- **Para concluir a task:** rodar o script com fotos reais, colar o `resultado.json` no chat, e o agente documenta a decisão em `specs/03-evidence-engine.md` seção 9.
