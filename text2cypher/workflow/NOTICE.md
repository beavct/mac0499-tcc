# NOTICE — Atribuição e mudanças

Este diretório (`text2cypher/workflow/`) é uma **obra derivada** do **CyVerACT**,
vendorizado e adaptado para este trabalho.

## Obra original

- **CyVerACT: An Agentic Cypher Translation Workflow over Knowledge Graphs**
- Autores: Christina-Maria Androna, Ioanna Mandilara, Eleftheria Arkadopoulou, Eleni Fotopoulou, Anastasios Zafeiropoulos, Symeon Papavassiliou (Institute of Communication and Computer Systems, National Technical University of Athens).
- Publicação: *Information Processing and Management*, v. 63, 2026, art. 104836. DOI: 10.1016/j.ipm.2026.104836.
- Repositório: GitLab `netmode/CyVerACT`.
- Licença: **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)** — ver `LICENSE`.

A biblioteca de validação **CyVer** (mesmos autores, também CC BY-SA 4.0) é usada como
dependência instalada via PyPI (`CyVer`), não vendorizada.

## Termos

Conforme a CC BY-SA 4.0: este derivado dá **atribuição** aos autores originais, indica
as **mudanças** feitas (abaixo) e é distribuído sob a **mesma licença** (share-alike).

## Mudanças em relação ao original

Em todos os arquivos vendorizados foi acrescentado um cabeçalho de proveniência e
removido código comentado sem uso. Além disso:

**Novos:** `Nodes/schema_rag.py` (substitui o `schema_filtering`), `config_workflow.py`, `executar.py`.

**Adaptados:**
- `graph.py` — usa o `schema_rag`; parâmetros do `StateGraph` atualizados para o langgraph 1.x.
- `Nodes/schema_retriever.py` — fallback por RAG com `k` maior, em vez do esquema completo.
- `Nodes/cypher_executor.py` — execução habilitada, com timeout e registro do erro.
- `Configuration/models.py` — só modelos abertos via API compatível com a OpenAI.
- `Nodes/cypher_generator.py`, `Nodes/cypher_corrector.py` — contagem de tokens pelo `langchain-core`; mensagem de início antes da chamada ao LLM.
- `Nodes/States/states.py`, `Nodes/output_generator.py` — campo `execution_error`.
- `Configuration/configurations.py` — campo `timeout_execucao`.
- `Nodes/unavailable_output.py` — `database_records` passa de `['']` a `None`.
- `Nodes/cyver_evaluator.py` — só comentários corrigidos (`k` e `n` estavam trocados).

**Sem alteração:** `Edges/conditional_edges_extended.py`.
