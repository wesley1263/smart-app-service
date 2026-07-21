# SPEC-00 — Visão de Produto

**Status:** validado em produção (documento de produto, não código)
**Depende de:** —

## 1. Contexto

Smart App é uma plataforma de aprendizagem adaptativa para crianças/adolescentes de 6–17 anos, baseada em pré-aprendizagem: a criança estuda o capítulo antes de ele ser dado em sala, transformando a aula no segundo contato com o conteúdo.

## 2. Tese central

"A aula deve ser o segundo contato da criança com o conhecimento, nunca o primeiro." O diferencial não é IA nem gamificação — é transformar o estudo em processo ativo, progressivo e adaptativo, com evidências físicas reais (escrita à mão, fala), antes da aula acontecer.

## 3. Arquitetura conceitual — os 5 motores

| Motor | Responsabilidade | Spec |
|---|---|---|
| Ingestion Engine | Scanner, OCR, limpeza, segmentação, embeddings, indexação do material escolar | `01-ingestion-engine.md` |
| Knowledge Engine | Transforma capítulo em Learning Nodes (unidade de conhecimento) | `02-knowledge-engine.md` |
| Evidence Engine | Coleta evidências: foto (mindmap, resumo), áudio (explicação Feynman), jogos, tempo | `03-evidence-engine.md` |
| Learning State Engine | Estima confiança de aprendizagem por Learning Node a partir das evidências | `04-learning-state-engine.md` |
| Generation Engine | Gera feedback, reestruturação cirúrgica, quiz e jogos — sob demanda (Camada 2) | `05-generation-engine.md` |

Fluxo geral: `Documento → Ingestion Engine → Knowledge Engine → Learning Nodes → Plano de Sessões → Estudo → Evidence Engine → Learning State Engine → Generation Engine → Próxima Sessão`.

## 4. Princípios fundamentais (inegociáveis)

1. A criança produz conhecimento (nunca só consome).
2. A aula é o segundo contato.
3. O papel é imutável — o progresso escrito nunca é invalidado.
4. A IA nunca pune; falso negativo é o pior erro possível.
5. A culpa nunca é da criança.
6. Toda interação gera evidências de aprendizagem.
7. O conhecimento evolui continuamente, de forma cirúrgica (nó a nó).
8. Idade calibra tudo: linguagem, densidade, tempo, tom.
9. A diversão é o motor do hábito, não a cereja do bolo.

## 5. Escopo do MVP

**Dentro:**
- Perfil de aluno (conta familiar prevista no dado, mas 1 app)
- Onboarding: tema de interesse + matéria + scanner + data de início na escola
- Camada 1: plano do capítulo (Learning Nodes + mindmap esperado + sessões)
- Estudo com validação por foto (mindmap), tom generoso
- Validação por áudio (Feynman) em pelo menos um ponto do fluxo
- Reestruturação cirúrgica de 1 Learning Node com confiança baixa
- Resumo à mão com foto + avaliação
- 1 jogo (forca) como recompensa de sessão
- Repetição espaçada com quiz gerado sob demanda
- Pomodoro calibrado por idade

**Fora do MVP (fases seguintes):**
- Visão do responsável (relatórios, insights, streak)
- Demais jogos (cruzadas, portas, chuva de meteoro)
- Notificações/gatilhos de rotina sofisticados
- Novos temas além da lista inicial (Minecraft, mangá, DC, Marvel)

**Pré-requisito antes de qualquer código de produto:** validar a taxa de acerto da leitura de manuscrito infantil (10–15 fotos reais → IA → medir acerto). Se isso falhar, o fluxo inteiro cai. Isso deve virar a primeira task executável do projeto (ver `tasks/`).

## 6. Riscos priorizados

1. Formação de hábito sem gatilho de prova (risco de produto, não técnico — mitigar com sessões curtas e recompensa real).
2. Leitura de manuscrito infantil (falsos negativos) — mitigar com threshold generoso + teste de viabilidade antes de codar.
3. Redundância/fricção no fluxo.
4. Escopo crescente — disciplina de MVP: 1 jogo, zero dashboard de responsável.

## 7. Métricas de sucesso do MVP

- Retenção orgânica na 2ª semana.
- Sessões completadas por semana por criança.
- Taxa de validação bem-sucedida na primeira foto.
- Nº de Learning Nodes reestruturados por capítulo.

## 8. Perguntas em aberto

- Estrutura de conta familiar: multi-tenant desde o MVP ou só o suficiente para não ter que migrar depois?
- Onde roda a inferência de visão/áudio (modelo próprio vs API externa)? Impacta custo e latência do Evidence Engine.
- Formato de armazenamento de fotos/áudios: blob storage externo (S3/GCS) referenciado por URL (`media_url`), não como binário no PostgreSQL — decidido em `adr/0002-stack-choice.md`.
