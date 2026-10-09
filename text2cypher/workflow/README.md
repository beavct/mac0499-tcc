# workflow — Pipeline Text-to-Cypher (sobre o CyVerACT)

Workflow que transforma a pergunta em Cypher, valida a consulta com o CyVer, corrige em laço e executa no Neo4j. É uma adaptação do **CyVerACT** (ver [atribuição](#licenca)). A principal troca é no nó de esquema: no lugar do filtro por nome, entra o RAG das propriedades ([`../dicionario/`](../dicionario)). Opcionalmente, um nó a mais ancora os nomes citados na pergunta nos valores que existem no grafo (Camada B).

## Conteúdo

1. [Fluxo](#fluxo)
2. [O que foi reusado e o que mudou](#reuso)
3. [Estrutura](#estrutura)
4. [Configuração e flags](#flags)
5. [Camada B: valores dos filtros](#camada_b)
6. [Como rodar](#rodar)
7. [Atribuição e licença](#licenca)
8. [Referências](#refs)

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

- **`schema_rag`** — busca no Chroma as propriedades relevantes e monta o esquema, junto da estrutura do grafo e da hierarquia territorial. Com `USAR_RAG` desligado, entra no lugar dele o **`schema_completo`**, que manda todas as propriedades, sem busca.
- **`value_grounding`** (opcional, Camada B) — entra entre o `schema_rag` e o `cypher_generator` e acrescenta ao esquema os valores reais dos nomes citados na pergunta (ver [Camada B](#camada_b)).
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
- **`value_grounding`** (novo, opcional): a Camada B, que não existe no CyVerACT;
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
├── teste_value_grounding.py   ← teste da Camada B com LLM falso (sem Ollama)
├── config_workflow.py         ← modelo, k, n e flags de ablação
├── Configuration/
│   ├── configurations.py      ← campos do config['configurable'] (referência)
│   └── models.py              ← fábricas de modelo (Ollama local, servidor externo)
├── Edges/
│   └── conditional_edges_extended.py   ← roteador da decisão do laço
└── Nodes/
    ├── States/states.py       ← formatos do estado (entrada, trabalho, saída)
    ├── schema_rag.py          ← NOVO: esquema por RAG (Camada A) ou completo (schema_completo)
    ├── value_grounding.py     ← NOVO: valores dos filtros (Camada B, opcional)
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
| Modelo | `MODEL_NAME` | `ollama_local` | chave em `Configuration/models.py` |
| `k` | `ATTEMPTS_W_FILTERED` | `5` | tentativas de correção com o esquema filtrado (valor do CyVerACT) |
| `n` | `TOTAL_ATTEMPTS` | `10` | tentativas totais antes de desistir (`k < n`; com `k > n`, o fallback nunca é acionado) |
| Timeout da execução | `TIMEOUT_EXECUCAO` | `60` | limite (s) para executar a query no Neo4j; ao estourar, o erro vai para `execution_error` |
| `k` do RAG | `TOP_K` | `20` | propriedades recuperadas por pergunta (definido em `../config.py`) |
| `k` do fallback | `TOP_K_FALLBACK` | `3×TOP_K` | propriedades recuperadas no `schema_retriever` (definido no próprio nó) |
| RAG das propriedades | `USAR_RAG` | `true` | liga a Camada A; desligado, o nó `schema_completo` manda todas as ~1.800 propriedades, o que só cabe no contexto de modelos grandes |
| Value grounding | `USAR_VALUE_GROUNDING` | `false` | liga a Camada B (`true`, `1` ou `sim`); desligada, o workflow é o de antes |

Só usamos modelos abertos, por uma API compatível com a da OpenAI. Os parâmetros de geração são os do CyVerACT (`temperature=0.01`, `top_p=0.9`, até 512 tokens):

| `MODEL_NAME` | Onde roda | Variáveis de ambiente |
|--------------|-----------|-----------------------|
| `ollama_local` | Ollama na própria máquina, sem custo | `OLLAMA_MODEL` (padrão `qwen2.5-coder:7b`), `OLLAMA_BASE_URL` (padrão `http://localhost:11434/v1`) |
| `servidor_externo` | qualquer servidor compatível com a API da OpenAI (ex.: servidor de pesquisa, vLLM) | `LLM_MODEL`, `LLM_BASE_URL`, `LLM_API_KEY` |

Pra usar outro modelo, é só adicionar uma fábrica em `models.py` e apontar o `MODEL_NAME` pra ela.

<a name="camada_b"></a>
## Camada B: valores dos filtros

A Camada B manda pro modelo os nomes de lugares e de equipamentos citados na pergunta, escritos do jeito que estão no grafo. Ela é opcional e vem desligada.

Ela existe porque o modelo tende a copiar o nome do jeito que veio na pergunta. Se a pergunta é "quantas escolas há em sao jose dos campos?" e ele escreve `{nm_mun: 'sao jose dos campos'}`, a consulta volta vazia, porque o grafo guarda `'São José dos Campos'`. O CyVer não reclama, já que a propriedade existe, então o erro só aparece no resultado.

Com a Camada B ligada, o esquema ganha um bloco assim no final:

```
Valores que existem no grafo para termos da pergunta (use um valor só se a pergunta estiver se referindo àquele lugar ou equipamento, e escreva-o exatamente como aparece aqui):
- "sao jose dos campos": Municipio.nm_mun = 'São José dos Campos'; Distrito.nm_dist = 'São José dos Campos'
```

### De onde vêm os nomes

Da lista `PROPRIEDADES_VALORES`, em `../config.py`: `nm_uf`, `nm_mun`, `nm_dist`, `nm_bairro` e o `nm_aparelho` das escolas e dos equipamentos de saúde. O Subdistrito fica de fora porque no grafo ele só tem código. São ~44 mil nomes, lidos do Neo4j na primeira pergunta e guardados em memória.

### Como a pergunta é comparada com os nomes

A ideia vem da camada semântica de Macedo et al. (SBBD 2026): comparar a pergunta com os valores reais das colunas, sem acento e sem maiúscula, e mandar os que batem num bloco do prompt. Lá, um LLM tira os nomes da pergunta antes; aqui a pergunta é comparada direto, como faz o CodeS (Li et al., 2024), então não tem uma chamada a mais ao modelo.

A comparação usa as funções do BRIDGE (Lin et al., 2020), copiadas em [`../dicionario/bridge.py`](../dicionario/bridge.py): pra cada nome, ele acha o maior trecho em comum com a pergunta e dá uma nota de 0 a 1. Ficam os nomes com nota a partir de 0,9, o mesmo valor do CodeS, então erros pequenos de digitação também passam:

| Pergunta | Valor encontrado |
|----------|------------------|
| "escolas em sao jose dos campos" | `Municipio.nm_mun = 'São José dos Campos'` |
| "UBS em Sorocab" | `Municipio.nm_mun = 'Sorocaba'` |
| "escolas em Mogi das Cruz" | `Municipio.nm_mun = 'Mogi das Cruzes'` |

Ficam no máximo 5 valores por coluna (o CodeS guarda até 25). Nas perguntas de teste, nenhuma coluna passou de 2, mas o limite maior deixa a pergunta citar vários lugares do mesmo tipo, como "escolas em Campinas, Sorocaba, Jundiaí e Santos".

### Nomes que são palavras comuns

Muitos lugares do estado têm nome de palavra comum: há um distrito chamado Saúde, um município chamado Quadra e um bairro chamado Centro. Sem cuidado, toda pergunta sobre "estabelecimentos de saúde" receberia o distrito Saúde. Por isso entram dois filtros, inspirados no TAGME (Ferragina e Scaiella, 2010):

- **o trecho maior ganha:** quando a pergunta tem `Vila Sônia`, o bairro `Vila` sai;
- **palavra comum só vale com o tipo do lugar antes:** se o nome é feito só de palavras das descrições do dicionário, ele só entra quando a pergunta diz antes que tipo de lugar é.

| Pergunta | Resultado |
|----------|-----------|
| "estabelecimentos de saúde em Campinas" | só Campinas, sem o distrito Saúde |
| "escolas no distrito da Saúde" | `Distrito.nm_dist = 'Saúde'` |
| "centros de saúde em Campinas" | só Campinas, sem o bairro Centro |

Em testes pequenos, a gente também tentou mandar esses nomes pro modelo com um aviso, deixando ele decidir se usava. Funcionou pior do que o filtro, então o filtro ficou. O bloco ainda pede pro modelo só usar um valor quando a pergunta estiver falando daquele lugar, pros casos que o filtro deixa passar.

Os tipos aceitos estão no próprio `PROPRIEDADES_VALORES` (`"distrito"`, `"bairro"`, `"municipio"`...), **sem acento**, porque a pergunta é comparada sem acento.

Nas 66 perguntas de [`../../perguntas/`](../../perguntas), só as duas que citam um lugar (Campinas e Vila Sônia) recebem valores.

Lembrando que o BRIDGE só olha a primeira vez que um nome aparece na pergunta. Em "centros de saúde no bairro Centro", ele pega o "centros" do começo, que o filtro descarta, e o bairro Centro fica de fora. É um caso raro, e consertar exigiria mudar o código copiado.

### Como usar

```bash
# workflow com a Camada B
cd text2cypher/workflow
USAR_VALUE_GROUNDING=true python executar.py "quantas escolas há em sao jose dos campos?"

# teste rápido da camada, com LLM falso (sem o Ollama)
python teste_value_grounding.py

# só os valores que uma pergunta recebe, sem rodar o workflow
cd ../dicionario
python valores.py "quantas escolas há em sao jose dos campos?"
```

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
ollama pull llama3.1:8b            # segundo modelo dos testes (~4,9 GB)
ollama pull qwen2.5-coder:1.5b     # opcional: bem menor (~1 GB), só para testar a integração
```

### Fazer uma pergunta

```bash
cd text2cypher/workflow
python executar.py "quantas escolas há em Campinas?"

# com outro modelo do Ollama:
OLLAMA_MODEL=llama3.1:8b python executar.py "quantas escolas há em Campinas?"
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
- Macedo et al., *Two-Layer RAG for Value Grounding and Schema Linking in LLM-Based Text-to-SQL Systems*, SBBD 2026 (camada semântica, base da Camada B)
- Li et al., *CodeS: Towards Building Open-source Language Models for Text-to-SQL*, [arXiv:2402.16347](https://arxiv.org/abs/2402.16347), 2024 (*value retriever* da Camada B)
- Lin, Socher e Xiong, *Bridging Textual and Tabular Data for Cross-Domain Text-to-SQL Semantic Parsing*, Findings of EMNLP 2020, [arXiv:2012.12627](https://arxiv.org/abs/2012.12627) (funções de casamento, em `../dicionario/bridge.py`)
- Ferragina e Scaiella, *TAGME*, CIKM 2010; versão estendida em [arXiv:1006.3498](https://arxiv.org/abs/1006.3498) (filtros da Camada B)
- [LangGraph — documentação](https://docs.langchain.com/oss/python/langgraph/overview)
- [Ollama — download](https://ollama.com/download)
- [Ollama — compatibilidade com a API da OpenAI](https://docs.ollama.com/api/openai-compatibility)
- [Qwen2.5-Coder na biblioteca do Ollama](https://ollama.com/library/qwen2.5-coder)
- [Llama 3.1 na biblioteca do Ollama](https://ollama.com/library/llama3.1)
