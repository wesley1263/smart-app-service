# ADR-0001 — Registrar decisões de arquitetura

**Status:** aceito

## Contexto
Um agente de IA implementando código a partir de specs vai tomar dezenas de micro-decisões técnicas (escolha de biblioteca, formato de fila, estratégia de índice). Sem registro, essas decisões se perdem e cada agente/sessão nova re-decide do zero, gerando inconsistência.

## Decisão
Toda decisão arquitetural não trivial — a que um agente futuro poderia razoavelmente decidir diferente — é registrada em `adr/NNNN-titulo.md`: contexto, decisão, consequências. ADRs não são reescritas; se uma decisão muda, cria-se uma nova ADR que supera a anterior (referenciando-a), seguindo o mesmo princípio de imutabilidade do produto ("o papel é imutável").

## Consequências
Qualquer agente, antes de decidir algo estrutural, deve checar `adr/` primeiro para não contradizer uma decisão já tomada.
