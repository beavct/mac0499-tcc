# Mapa de Consultas Analíticas — PostgreSQL vs. Neo4j

Este documento apresenta as 60 consultas socioespaciais que compõem o benchmark comparativo entre o modelo relacional (PostgreSQL/PostGIS) e o modelo orientado a grafos (Neo4j). As consultas exploram cruzamentos entre microdados de equipamentos públicos (INEP 2024, CNES 2025) e agregados censitários do IBGE 2022, operando sobre todo o estado de São Paulo.

Cada consulta existe em 3 formatos:
- `linguagem-natural/` — como um gestor público perguntaria (sem códigos técnicos)
- `postgreSQL/` — query SQL com JOINs espaciais via PostGIS
- `neo4j-cypher/` — query Cypher com travessias no grafo de propriedades

## Níveis de agregação

As consultas foram propositalmente distribuídas entre diferentes níveis de agregação territorial, para exercitar a hierarquia do grafo em diversas profundidades:

| Nível | O que a consulta retorna | Nº de consultas |
|-------|--------------------------|-----------------|
| **Município** | resultado agregado por município (visão macro estadual) | 8 |
| **Distrito** | agregado por distrito (análise intra-municipal) | 16 |
| **Subdistrito** | agregado por subdistrito | 2 |
| **Bairro** | agregado por bairro | 4 |
| **Setor** | agregado por setor censitário | 14 |
| **Lista** | listagem de equipamentos individuais ou pares (ex.: escola × distrito) | 16 |

Toda consulta que retorna um nível abaixo do município também retorna o município correspondente, para tornar o resultado autoexplicativo.

---

## Eixo 1 — Educação Básica (25 consultas)

Cruzamento entre variáveis de oferta escolar (turmas por etapa, dependência administrativa, infraestrutura) e indicadores de vulnerabilidade territorial.

### 1.1 Infraestrutura e Distribuição Escolar

| # | Nível | Pergunta |
|---|-------|----------|
| Q01 | Município | Quantas escolas de educação básica existem em cada município? |
| Q02 | Município | Qual é a proporção de escolas públicas em relação às privadas em cada município? |
| Q03 | Lista | Quais escolas não possuem esgoto ligado à rede pública nem fossa séptica? |
| Q04 | Município | Quantas escolas possuem quadra de esportes, seja coberta ou descoberta, em cada município? |
| Q05 | Lista | Quais escolas atendem simultaneamente turmas de Creche e turmas de Ensino Médio? |

### 1.2 Vazios Educacionais e Vulnerabilidade Habitacional

| # | Nível | Pergunta |
|---|-------|----------|
| Q06 | Setor | Quais setores possuem as maiores populações de adultos não alfabetizados e não contam com nenhuma escola? |
| Q09 | Lista | Quais escolas de Ensino Fundamental estão em setores onde mais de 50 moradores residem em domicílios improvisados? |
| Q12 | Distrito | Qual a razão entre turmas de creche e a população de crianças de 0 a 4 anos em cada distrito do estado? |
| Q13 | Lista | Quantos domicílios com mais de 5 moradores estão próximos de escolas que ofertam ensino EAD? |
| Q17 | Setor | Quantas escolas de Ensino Médio estão em setores onde predominam moradores em casas de vila ou condomínio? |
| Q23 | Setor | Quantas escolas da rede pública estão em setores onde os domicílios não possuem banheiro de uso exclusivo? |

### 1.3 Primeira Infância e Arranjos Familiares

| # | Nível | Pergunta |
|---|-------|----------|
| Q08 | Distrito | Quantas escolas de Educação Infantil oferecem turmas em tempo integral em distritos com famílias estendidas? |
| Q14 | Lista | Quais escolas privadas de Educação Infantil estão em distritos com alta população de crianças de 0 a 4 anos? |
| Q15 | Bairro | Quantas turmas de creche em tempo integral existem em bairros com alta presença de mulheres chefes de família? |
| Q19 | Subdistrito | Quais subdistritos apresentam a maior disparidade na oferta de turmas de Educação Infantil entre seus setores? |

### 1.4 Alfabetização, EJA e Ensino Noturno

| # | Nível | Pergunta |
|---|-------|----------|
| Q11 | Lista | Quais escolas com Ensino Médio noturno estão em setores com jovens de 15 a 19 anos não alfabetizados? |
| Q18 | Município | Qual a distribuição de turmas de EJA Médio por município, confrontando com a população analfabeta de 15 a 19 anos? |
| Q21 | Lista | Quais escolas públicas estaduais com EJA Fundamental estão em setores com moradores em cortiços? |

### 1.5 Educação Inclusiva e Equidade Racial

| # | Nível | Pergunta |
|---|-------|----------|
| Q07 | Lista | Quais escolas públicas de Ensino Médio diurno estão em setores com famílias indígenas responsáveis por domicílios? |
| Q16 | Distrito | Quais distritos têm os maiores vazios de Educação Especial Inclusiva frente ao volume de jovens de 15 a 19 anos? |
| Q20 | Distrito | Qual a proporção de escolas com Educação Especial Inclusiva em cada distrito? |
| Q22 | Distrito | Como se comporta a oferta de turmas de Ensino Fundamental diurno em distritos com alta concentração de população parda? |

### 1.6 Travessia Multi-hop (vantagem do grafo)

| # | Nível | Pergunta |
|---|-------|----------|
| Q10 | Lista | Para cada escola que oferta Ensino Médio, quantas escolas de Ensino Fundamental existem no mesmo distrito? |
| Q24 | Lista | Quais escolas sem laboratório de ciências estão em distritos onde pelo menos 5 outras escolas possuem laboratório de ciências? |
| Q25 | Distrito | Quais escolas sem quadra de esportes estão em distritos onde pelo menos 5 outras escolas possuem quadra? |

---

## Eixo 2 — Saúde Pública e Privada (25 consultas)

Cruzamento entre variáveis de oferta assistencial (internação, ambulatório, urgência, vigilância, diagnose) por tipo de convênio e indicadores territoriais do Censo 2022.

### 2.1 Desertos Sanitários e Infraestrutura Urbana

| # | Nível | Pergunta |
|---|-------|----------|
| Q03 | Setor | Quais setores com mais de 1.000 moradores não possuem nenhum estabelecimento de saúde? |
| Q10 | Distrito | Quais distritos com mais de 50.000 habitantes possuem menos de 3 ambulatórios pelo SUS? |
| Q14 | Setor | Quais setores sem abastecimento de água pela rede geral possuem atendimento ambulatorial por plano público? |
| Q18 | Distrito | Quais distritos têm domicílios sem banheiro e qual a presença de Vigilância em Saúde SUS? |
| Q24 | Setor | Quantas unidades de Urgência por gratuidade estão em setores com esgotamento precário? |
| Q25 | Município | Quantas pessoas em setores rurais contam com atendimento ambulatorial pelo SUS, por município? |

### 2.2 Atenção a Faixas Etárias Extremas

| # | Nível | Pergunta |
|---|-------|----------|
| Q04 | Lista | Quais unidades com plano privado estão em setores com alta população infantil feminina de 0 a 4 anos? |
| Q06 | Setor | Quais setores com alta população de idosos de 80 anos ou mais não possuem nenhuma unidade de Urgência pelo SUS? |
| Q09 | Lista | Quais unidades de Vigilância em Saúde SUS estão em territórios com idosos de 70 anos ou mais? |
| Q11 | Lista | Quais unidades de Urgência SUS estão em setores com alta densidade de idosos de 80 anos ou mais? |

### 2.3 Vulnerabilidade Habitacional e Populações Minoritárias

| # | Nível | Pergunta |
|---|-------|----------|
| Q01 | Município | Quais municípios registram mais domicílios improvisados e qual a oferta de internação SUS? |
| Q05 | Setor | Quantas unidades "Outros — SUS" cobrem setores com moradores em cortiços? |
| Q12 | Distrito | Quantos centros de Diagnose e Terapia SUS existem em distritos com alta população preta? |
| Q17 | Setor | Quantas unidades de Urgência por plano público cobrem setores com população parda expressiva? |
| Q23 | Distrito | Como se comporta a oferta de leitos com gratuidade em distritos com população de raça amarela? |

### 2.4 Convênios, Leitos e Perfil Socioeconômico

| # | Nível | Pergunta |
|---|-------|----------|
| Q07 | Distrito | Qual o total de domicílios permanentes em distritos com mais de 5 unidades de internação SUS? |
| Q08 | Bairro | Quais bairros de Campinas possuem internação por gratuidade em territórios com chefia feminina? |
| Q13 | Lista | Quais unidades de internação por plano privado estão em setores com adensamento vertical? |
| Q15 | Bairro | Quantas unidades de Urgência privada estão em bairros com responsáveis de raça amarela? |
| Q19 | Distrito | Quantas unidades de internação por plano público existem no distrito da Vila Sônia? |

### 2.5 Distribuição Geográfica e Análise Regional

| # | Nível | Pergunta |
|---|-------|----------|
| Q02 | Lista | Quais unidades ambulatoriais SUS estão em setores com jovens analfabetos de 15 a 19 anos? |
| Q16 | Distrito | Qual a proporção de domicílios em esgotamento sanitário precário por fossa rudimentar frente à população de cada distrito do estado? |
| Q20 | Lista | Para cada unidade de internação pelo SUS, quantas unidades de atendimento ambulatorial pelo SUS existem no mesmo distrito? |
| Q21 | Município | Qual a distribuição de Vigilância em Saúde por plano público em cada município vs. analfabetismo adulto? |
| Q22 | Subdistrito | Quais subdistritos registram a maior disparidade na oferta de leitos de internação SUS? |

---

## Eixo 3 — Intersetorial (10 consultas)

Cruzamento simultâneo entre equipamentos de educação e saúde no mesmo território, identificando vazios, desbalanceamentos e coberturas complementares.

| # | Nível | Pergunta |
|---|-------|----------|
| Q01 | Setor | Quais setores possuem escola pública mas nenhum estabelecimento de saúde ambulatorial SUS? |
| Q02 | Setor | Quais setores com alta vulnerabilidade habitacional não possuem nenhum equipamento público? |
| Q03 | Distrito | Quais distritos têm mais de 10 escolas mas menos de 3 unidades de saúde ambulatorial SUS? |
| Q04 | Bairro | Quais bairros possuem creches mas nenhuma unidade de saúde ambulatorial SUS? |
| Q05 | Município | Qual a razão entre escolas e unidades de saúde ambulatorial SUS por município? |
| Q06 | Setor | Quais setores com idosos possuem EJA mas não possuem Urgência SUS? |
| Q07 | Setor | Quais setores com escola pública e moradores em domicílios improvisados não possuem nenhuma unidade de saúde ambulatorial pelo SUS? |
| Q08 | Distrito | Quais distritos com crianças em domicílios improvisados possuem creches e internação SUS? |
| Q09 | Setor | Qual o total de equipamentos públicos por setor nos territórios mais populosos e desassistidos? |
| Q10 | Distrito | Em cada distrito do estado, qual a presença de responsáveis indígenas por domicílio, de escolas públicas de Ensino Fundamental e de unidades de saúde ambulatorial pelo SUS? |

---

## Fontes de Dados

| Fonte | Ano | Conteúdo |
|-------|-----|----------|
| IBGE — Censo Demográfico | 2022 | Malha territorial, setores censitários, variáveis socioeconômicas |
| INEP — Censo Escolar | 2024 | Microdados de educação básica (escolas, turmas, matrículas, infraestrutura) |
| CNES/DATASUS | 2025 | Cadastro de estabelecimentos de saúde e atendimentos por convênio |

## Recorte Territorial

Todo o estado de São Paulo (UF 35) — 645 municípios. Duas consultas de saúde restringem-se propositalmente a um recorte específico, como exemplos de consulta pontual: a Q08 (bairros de Campinas) e a Q19 (distrito da Vila Sônia, em São Paulo).
