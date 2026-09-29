# workflow — Pipeline Text-to-Cypher (sobre o CyVerACT)

Workflow que transforma a pergunta em Cypher, valida a consulta com o CyVer, corrige em laço e executa no Neo4j. É uma adaptação do **CyVerACT** (ver [atribuição](#licenca)). A principal troca é no nó de esquema: no lugar do filtro por nome, entra o RAG das propriedades ([`../dicionario/`](../dicionario)).

## Conteúdo

1. [Fluxo](#fluxo)
2. [O que foi reusado e o que mudou](#reuso)
3. [Estrutura](#estrutura)
4. [Configuração e flags](#flags)
5. [Como rodar](#rodar)
6. [Atribuição e licença](#licenca)
7. [Referências](#refs)

---

<a name="fluxo"></a>
## Fluxo

```
START
  └─ schema_rag ──> cypher_generator ──> cyver_evaluator ──(decisão)──┐
                        ▲                                             │
     schema_retriever ──┘                                            │
           ▲          ┌──────── cypher_corrector <───────────────────┤ (com erro, Retry < k)
           │          └──> cyver_evaluator (revalida)                 │
           └───────────────(escalona: Retry = k)────────────────────┤
                                                                     │
                        cypher_executor ──> output_generator ──> END ◄┘ (sem erro)
                        unavailable_output ──> END ◄──────────────────── (Retry = n)
```

- **`schema_rag`** — busca no Chroma as propriedades relevantes e monta o esquema, junto da estrutura do grafo.
- **`cypher_generator`** — LLM gera o Cypher a partir do esquema e da pergunta.
- **`cyver_evaluator`** — roda os validadores do CyVer (sintaxe, esquema, propriedades) **sem executar** a query e junta os erros.
- **`cypher_corrector`** — LLM reescreve a query a partir dos erros.
- **`schema_retriever`** — fallback: quando as tentativas com o esquema filtrado acabam, roda o RAG novamente com um `k` maior.
- **`cypher_executor` / `output_generator` / `unavailable_output`** — executa a query válida e monta a saída (ou a de desistência).

O laço é controlado por `k` (`attempts_w_filtered`) e `n` (`total_attempts`), como na Fig. 2 do CyVerACT.

<a name="reuso"></a>
## O que foi reusado e o que mudou

A lógica do CyVerACT continua a mesma: o gerador, a validação pelo CyVer, o laço de correção com `k` e `n` e as saídas. O que mudou:

- **`schema_rag`** (novo): substitui o filtro de esquema por nome pelo RAG das propriedades;
- **`schema_retriever`**: o fallback amplia o RAG (`k` maior) em vez de mandar o esquema completo, que teria ~1.800 propriedades;
- **`cypher_executor`**: a execução, que vinha desligada no original, agora roda, com timeout e registro do erro;
- **`models.py`**: só modelos abertos, sem fine-tuning, via API compatível com a da OpenAI;
- ajustes pontuais para as versões atuais do `langchain-core` e do `langgraph`.

A lista por arquivo está em [`NOTICE.md`](NOTICE.md).

<a name="estrutura"></a>
## Estrutura

```
workflow/
├── README.md
├── LICENSE                    ← CC BY-SA 4.0 (do CyVerACT)
├── NOTICE.md                  ← atribuição e mudanças feitas
├── graph.py                   ← montagem do grafo de estados (LangGraph)
├── executar.py                ← ponto de entrada (pergunta → Cypher → execução)
├── teste_rapido.py            ← teste do fluxo completo com LLM falso (sem Ollama)
├── config_workflow.py         ← modelo, k, n e flags de ablação
├── Configuration/
│   ├── configurations.py      ← campos do config['configurable'] (referência)
│   └── models.py              ← fábricas de modelo (Ollama local, servidor externo)
├── Edges/
│   └── conditional_edges_extended.py   ← roteador da decisão do laço
└── Nodes/
    ├── States/states.py       ← formatos do estado (entrada, trabalho, saída)
    ├── schema_rag.py          ← NOVO: esquema por RAG (Camada A)
    ├── schema_retriever.py    ← fallback (RAG com k maior)
    ├── cypher_generator.py    ← LLM gera o Cypher
    ├── cyver_evaluator.py     ← validação CyVer e decisão do laço
    ├── cypher_corrector.py    ← LLM corrige o Cypher a partir dos erros
    ├── cypher_executor.py     ← executa no Neo4j (com timeout)
    ├── output_generator.py    ← saída com consulta válida
    └── unavailable_output.py  ← saída de desistência
```

<a name="flags"></a>
## Configuração e flags

Definidas em `config_workflow.py` (ajustáveis por variável de ambiente):

| Flag | Env | Default | O que faz |
|------|-----|---------|-----------|
| Modelo | `MODEL_NAME` | `qwen_local` | chave em `Configuration/models.py` |
| `k` | `ATTEMPTS_W_FILTERED` | `5` | tentativas de correção com o esquema filtrado (valor do CyVerACT) |
| `n` | `TOTAL_ATTEMPTS` | `10` | tentativas totais antes de desistir (`k < n`; com `k > n`, o fallback nunca é acionado) |
| Timeout da execução | `TIMEOUT_EXECUCAO` | `60` | limite (s) para executar a query no Neo4j; ao estourar, o erro vai para `execution_error` |
| `k` do RAG | `TOP_K` | `20` | propriedades recuperadas por pergunta (definido em `../config.py`) |
| `k` do fallback | `TOP_K_FALLBACK` | `3×TOP_K` | propriedades recuperadas no `schema_retriever` (definido no próprio nó) |
| Value grounding | `USAR_VALUE_GROUNDING` | `false` | gancho para a Camada B (ainda não implementada) |

Só usamos modelos abertos, por uma API compatível com a da OpenAI. Os parâmetros de geração são os do CyVerACT (`temperature=0.01`, `top_p=0.9`, até 512 tokens):

| `MODEL_NAME` | Onde roda | Variáveis de ambiente |
|--------------|-----------|-----------------------|
| `qwen_local` | Ollama na própria máquina, sem custo | `OLLAMA_MODEL` (padrão `qwen2.5-coder:7b`), `OLLAMA_BASE_URL` (padrão `http://localhost:11434/v1`) |
| `servidor_externo` | qualquer servidor compatível com a API da OpenAI (ex.: servidor de pesquisa, vLLM) | `LLM_MODEL`, `LLM_BASE_URL`, `LLM_API_KEY` |

Pra usar outro modelo, é só adicionar uma fábrica em `models.py` e apontar o `MODEL_NAME` pra ela.

<a name="rodar"></a>
## Como rodar

Antes de rodar, você precisa de: Neo4j carregado (ver [`../../etl/`](../../etl)), índice do Chroma construído (ver [`../dicionario/`](../dicionario)), dependências instaladas (`compartilhado/requirements.txt`) e o [Ollama](https://ollama.com) rodando com o modelo baixado (abaixo).

### Instalar e subir o Ollama

**1. Instalar** (uma vez só):

```bash
# macOS
brew install ollama

# Debian/Ubuntu (script oficial)
curl -fsSL https://ollama.com/install.sh | sh

# Arch Linux / Manjaro
sudo pacman -S ollama
```

**2. Subir o servidor**, com uma janela de contexto maior (ver aviso abaixo). Deixe rodando num terminal à parte:

```bash
OLLAMA_CONTEXT_LENGTH=16384 ollama serve
```

No Linux, a instalação pode ter criado um serviço do Ollama que já sobe sozinho. Se o comando acima reclamar que a porta está em uso, pare o serviço antes com `sudo systemctl stop ollama`.

**3. Baixar o modelo** (uma vez só; com o servidor no ar):

```bash
ollama pull qwen2.5-coder:7b       # modelo padrão (~4,7 GB)
ollama pull qwen2.5-coder:1.5b     # opcional: bem menor (~1 GB), só para testar a integração
```

### Fazer uma pergunta

```bash
cd text2cypher/workflow
python executar.py "quantas escolas há em Campinas?"

# com outro modelo do Ollama:
OLLAMA_MODEL=qwen2.5-coder:1.5b python executar.py "quantas escolas há em Campinas?"
```

Rode sempre de dentro de `text2cypher/workflow/`: os módulos usam imports relativos a essa pasta, como no CyVerACT original.

Pra conferir se está tudo funcionando **sem** o Ollama, rode o teste rápido. Um LLM falso devolve primeiro uma consulta com uma propriedade que não existe e depois uma válida. O script confere o caminho percorrido (gera → CyVer reprova → corrige → aprova → executa) e o resultado.

```bash
python teste_rapido.py
```

**Contexto do Ollama:** o esquema enviado ao modelo tem alguns milhares de tokens. Por padrão, o Ollama usa uma janela de contexto pequena e corta o excesso sem avisar. Por isso o `OLLAMA_CONTEXT_LENGTH=16384` ao subir o servidor.

A primeira pergunta de cada execução demora mais: é nela que o modelo de embedding é carregado e a estrutura do grafo é lida do Neo4j. As seguintes reaproveitam os dois.

<a name="licenca"></a>
## Atribuição e licença

Esta pasta é uma obra derivada do **CyVerACT** (Androna et al., *Information Processing and Management*, 2026, DOI 10.1016/j.ipm.2026.104836; GitLab `netmode/CyVerACT`), sob **CC BY-SA 4.0**. A adaptação mantém a mesma licença (share-alike) e credita os autores. A lista de mudanças está no [`NOTICE.md`](NOTICE.md), e o texto da licença, no [`LICENSE`](LICENSE).

<a name="refs"></a>
## Referências

- [CyVerACT — artigo](https://doi.org/10.1016/j.ipm.2026.104836) (Androna et al., *Information Processing and Management*, 2026) e repositório GitLab `netmode/CyVerACT`
- [LangGraph — documentação](https://docs.langchain.com/oss/python/langgraph/overview)
- [Ollama — download](https://ollama.com/download)
- [Ollama — compatibilidade com a API da OpenAI](https://docs.ollama.com/api/openai-compatibility)
- [Qwen2.5-Coder na biblioteca do Ollama](https://ollama.com/library/qwen2.5-coder)
