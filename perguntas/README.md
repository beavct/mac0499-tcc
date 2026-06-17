# Mapa de Consultas Analíticas — PostgreSQL vs. Neo4j

Este documento apresenta as 60 consultas socioespaciais que compõem o benchmark comparativo entre o modelo relacional (PostgreSQL/PostGIS) e o modelo orientado a grafos (Neo4j). As consultas exploram cruzamentos entre microdados de equipamentos públicos (INEP 2024, CNES 2025) e agregados censitários do IBGE 2022, operando sobre os municípios de São Paulo, Campinas e São Bernardo do Campo.

Cada consulta existe em 3 formatos:
- `linguagem-natural/` — como um gestor público perguntaria (sem códigos técnicos)
- `postgreSQL/` — query SQL com JOINs espaciais via PostGIS
- `neo4j-cypher/` — query Cypher com travessias no grafo de propriedades

---

## Eixo 1 — Educação Básica (25 consultas)

Cruzamento entre variáveis de oferta escolar (turmas por etapa, dependência administrativa, infraestrutura) e indicadores de vulnerabilidade territorial.

### 1.1 Infraestrutura e Distribuição Escolar

| # | Pergunta |
|---|----------|
| Q01 | Quantas escolas de educação básica existem em cada distrito? |
| Q02 | Qual é a proporção de escolas públicas em relação às privadas em cada município? |
| Q03 | Quais escolas não possuem esgoto ligado à rede pública nem fossa séptica? |
| Q04 | Quantas escolas possuem quadra de esportes, seja coberta ou descoberta, em cada distrito? |
| Q05 | Quais escolas atendem simultaneamente turmas de Creche e turmas de Ensino Médio? |

### 1.2 Vazios Educacionais e Vulnerabilidade Habitacional

| # | Pergunta |
|---|----------|
| Q06 | Quais setores possuem as maiores populações de adultos não alfabetizados e não contam com nenhuma escola? |
| Q09 | Quais escolas de Ensino Fundamental estão em setores onde mais de 50 moradores residem em domicílios improvisados? |
| Q12 | Quais distritos têm mais de 5.000 domicílios com crianças de 0 a 9 anos mas menos de 3 escolas com creche? |
| Q13 | Quantos domicílios com mais de 5 moradores estão próximos de escolas que ofertam ensino EAD? |
| Q17 | Quantas escolas de Ensino Médio estão em setores onde predominam moradores em casas de vila ou condomínio? |
| Q23 | Quantas escolas da rede pública estão em setores onde os domicílios não possuem banheiro de uso exclusivo? |
| Q24 | Quantas pessoas residem em setores urbanos que contam com escolas oferecendo Ensino Fundamental integral? |

### 1.3 Primeira Infância e Arranjos Familiares

| # | Pergunta |
|---|----------|
| Q08 | Quantas escolas de Educação Infantil oferecem turmas em tempo integral em distritos com famílias estendidas? |
| Q14 | Quais escolas privadas de Educação Infantil estão em distritos com alta população de crianças de 0 a 4 anos? |
| Q15 | Quantas turmas de creche em tempo integral existem em bairros com alta presença de mulheres chefes de família? |
| Q19 | Quais distritos apresentam a maior disparidade na oferta de turmas de Educação Infantil entre seus setores? |

### 1.4 Alfabetização, EJA e Ensino Noturno

| # | Pergunta |
|---|----------|
| Q11 | Quais escolas com Ensino Médio noturno estão em setores com jovens de 15 a 19 anos não alfabetizados? |
| Q18 | Qual a distribuição de turmas de EJA Médio por município, confrontando com a população analfabeta de 15 a 19 anos? |
| Q21 | Quais escolas públicas estaduais com EJA Fundamental estão em setores com moradores em cortiços? |

### 1.5 Educação Inclusiva e Equidade Racial

| # | Pergunta |
|---|----------|
| Q07 | Quais escolas públicas de Ensino Médio diurno estão em setores com famílias indígenas responsáveis por domicílios? |
| Q10 | Quantas turmas de Educação Especial Exclusiva existem em setores com moradores em cortiços? |
| Q16 | Quais distritos têm os maiores vazios de Educação Especial Inclusiva frente ao volume de jovens de 15 a 19 anos? |
| Q20 | Qual a proporção de escolas com Educação Especial Inclusiva em cada distrito? |
| Q22 | Como se comporta a oferta de turmas de Ensino Fundamental diurno em distritos com alta concentração de população parda? |

### 1.6 Travessia Multi-hop (vantagem do grafo)

| # | Pergunta |
|---|----------|
| Q25 | Quais escolas sem quadra de esportes estão em distritos onde pelo menos 5 outras escolas possuem quadra? |

---

## Eixo 2 — Saúde Pública e Privada (25 consultas)

Cruzamento entre variáveis de oferta assistencial (internação, ambulatório, urgência, vigilância, diagnose) por tipo de convênio e indicadores territoriais do Censo 2022.

### 2.1 Desertos Sanitários e Infraestrutura Urbana

| # | Pergunta |
|---|----------|
| Q03 | Quais setores com mais de 1.000 moradores não possuem nenhum estabelecimento de saúde? |
| Q10 | Quais distritos com mais de 50.000 habitantes possuem menos de 3 ambulatórios pelo SUS? |
| Q14 | Quais setores sem abastecimento de água pela rede geral possuem atendimento ambulatorial por plano público? |
| Q18 | Quais distritos têm domicílios sem banheiro e qual a presença de Vigilância em Saúde SUS? |
| Q24 | Quantas unidades de Urgência por gratuidade estão em setores com esgotamento precário? |
| Q25 | Quantas pessoas em setores rurais contam com atendimento ambulatorial pelo SUS? |

### 2.2 Atenção a Faixas Etárias Extremas

| # | Pergunta |
|---|----------|
| Q04 | Quais unidades com plano privado estão em setores com alta população infantil feminina de 0 a 4 anos? |
| Q09 | Quais unidades de Vigilância em Saúde SUS estão em territórios com idosos de 70 anos ou mais? |
| Q11 | Quais unidades de Urgência SUS estão em setores com alta densidade de idosos de 80 anos ou mais? |

### 2.3 Vulnerabilidade Habitacional e Populações Minoritárias

| # | Pergunta |
|---|----------|
| Q01 | Quais municípios registram mais domicílios improvisados e qual a oferta de internação SUS? |
| Q05 | Quantas unidades "Outros — SUS" cobrem setores com moradores em cortiços? |
| Q12 | Quantos centros de Diagnose e Terapia SUS existem em distritos com alta população preta? |
| Q17 | Quantas unidades de Urgência por plano público cobrem setores com população parda expressiva? |
| Q20 | Quais unidades de Diagnose e Terapia privada estão em setores com habitações improvisadas? |
| Q23 | Como se comporta a oferta de leitos com gratuidade em distritos com população de raça amarela? |

### 2.4 Convênios, Leitos e Perfil Socioeconômico

| # | Pergunta |
|---|----------|
| Q06 | Quantas pessoas em setores urbanos dependem de atendimento ambulatorial por gratuidade? |
| Q07 | Qual o total de domicílios permanentes em distritos com mais de 5 unidades de internação SUS? |
| Q08 | Quais bairros de Campinas possuem internação por gratuidade em territórios com chefia feminina? |
| Q13 | Quais unidades de internação por plano privado estão em setores com adensamento vertical? |
| Q15 | Quantas unidades de Urgência privada estão em bairros com responsáveis de raça amarela? |
| Q19 | Quantas unidades de internação por plano público existem no distrito da Vila Sônia? |

### 2.5 Distribuição Geográfica e Análise Regional

| # | Pergunta |
|---|----------|
| Q02 | Quais unidades ambulatoriais SUS estão em setores com jovens analfabetos de 15 a 19 anos? |
| Q16 | Quais unidades de Vigilância por plano privado estão em bairros com casas de vila/condomínio? |
| Q21 | Qual a distribuição de Vigilância em Saúde por plano público em cada distrito vs. analfabetismo adulto? |
| Q22 | Quais subdistritos registram a maior disparidade na oferta de leitos de internação SUS? |

---

## Eixo 3 — Intersetorial (10 consultas)

Cruzamento simultâneo entre equipamentos de educação e saúde no mesmo território, identificando vazios, desbalanceamentos e coberturas complementares.

| # | Pergunta |
|---|----------|
| Q01 | Quais setores possuem escola pública mas nenhum estabelecimento de saúde ambulatorial SUS? |
| Q02 | Quais setores com alta vulnerabilidade habitacional não possuem nenhum equipamento público? |
| Q03 | Quais distritos têm mais de 10 escolas mas menos de 3 unidades de saúde ambulatorial SUS? |
| Q04 | Quais bairros possuem creches mas nenhuma unidade de saúde ambulatorial SUS? |
| Q05 | Qual a razão entre escolas e unidades de saúde ambulatorial SUS por distrito? |
| Q06 | Quais setores com idosos possuem EJA mas não possuem Urgência SUS? |
| Q07 | Quais setores concentram escolas sem esgoto e unidades de Vigilância Sanitária SUS? |
| Q08 | Quais distritos com crianças em domicílios improvisados possuem creches e internação SUS? |
| Q09 | Qual o total de equipamentos públicos por setor nos territórios mais populosos e desassistidos? |
| Q10 | Quais distritos possuem escolas públicas e saúde SUS em setores com famílias indígenas? |

---

## Fontes de Dados

| Fonte | Ano | Conteúdo |
|-------|-----|----------|
| IBGE — Censo Demográfico | 2022 | Malha territorial, setores censitários, variáveis socioeconômicas |
| INEP — Censo Escolar | 2024 | Microdados de educação básica (escolas, turmas, matrículas, infraestrutura) |
| CNES/DATASUS | 2025 | Cadastro de estabelecimentos de saúde e atendimentos por convênio |

## Recorte Territorial

- São Paulo (cd_mun: 3550308)
- Campinas (cd_mun: 3548708)
- São Bernardo do Campo (cd_mun: 3509502)
