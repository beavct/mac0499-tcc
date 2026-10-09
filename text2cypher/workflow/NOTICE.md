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

**Novos:** `Nodes/schema_rag.py` (substitui o `schema_filtering`), `Nodes/value_grounding.py`
(Camada B, opcional; não tem equivalente no CyVerACT), `config_workflow.py`, `executar.py`.

**Adaptados:**
- `graph.py` — usa o `schema_rag`; parâmetros do `StateGraph` atualizados para o langgraph 1.x; com `USAR_VALUE_GROUNDING`, põe o `value_grounding` entre o `schema_rag` e o `cypher_generator`.
- `Nodes/schema_retriever.py` — fallback por RAG com `k` maior, em vez do esquema completo; mantém os valores da Camada B no esquema novo.
- `Nodes/cypher_executor.py` — execução habilitada, com timeout e registro do erro.
- `Configuration/models.py` — só modelos abertos via API compatível com a OpenAI.
- `Nodes/cypher_generator.py`, `Nodes/cypher_corrector.py` — contagem de tokens pelo `langchain-core`; mensagem de início antes da chamada ao LLM.
- `Nodes/States/states.py`, `Nodes/output_generator.py` — campo `execution_error`; no `states.py`, também o `grounded_values` (Camada B).
- `Configuration/configurations.py` — campo `timeout_execucao`.
- `Nodes/unavailable_output.py` — `database_records` passa de `['']` a `None`.
- `Nodes/cyver_evaluator.py` — só comentários corrigidos (`k` e `n` estavam trocados).

**Sem alteração:** `Edges/conditional_edges_extended.py`.

## Outros códigos de terceiros

Fora deste diretório, a Camada B (`../dicionario/valores.py`) usa `../dicionario/bridge.py`,
que tem outra origem e outra licença, e por isso **não** está sob a CC BY-SA 4.0:

- **Funções de casamento do BRIDGE** (Lin, Socher e Xiong, 2020), copiadas de
  `salesforce/TabularSemanticParsing` (`src/common/content_encoder.py` e `src/utils/utils.py`).
  Licença: **BSD 3-Clause**, Copyright (c) 2020, Salesforce.com, Inc. O texto completo da
  licença está no cabeçalho do arquivo, como ela exige.
- **Lista de stopwords em português do Snowball**, Copyright (c) 2001, Dr Martin Porter, e
  (c) 2002, Richard Boulton. Licença: **BSD**, também reproduzida no cabeçalho.

As duas licenças são permissivas: permitem copiar, alterar e redistribuir o código junto de
um projeto sob outra licença, desde que o aviso de copyright, as condições e o termo de
isenção de garantia sejam mantidos. As alterações feitas (só as funções usadas, num arquivo
só, e as stopwords e palavras comuns em português) estão listadas no cabeçalho.

A comparação segue a etapa fina do *value retriever* do CodeS (Li et al., 2024), com a mesma
nota mínima (0,9), mas nenhum código do CodeS foi copiado (o repositório dele é Apache 2.0):
o `valores.py` foi escrito por nós, e guarda até 5 valores por coluna, em vez de 25.
