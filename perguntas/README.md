# Mapa de Consultas Analíticas — PostgreSQL vs. Neo4j

Este documento apresenta as **66 consultas** socioespaciais que compõem o benchmark comparativo entre o modelo relacional (PostgreSQL/PostGIS) e o modelo orientado a grafos (Neo4j). As consultas exploram cruzamentos entre microdados de equipamentos públicos (INEP 2024, CNES 2025) e agregados censitários do IBGE 2022, operando sobre todo o estado de São Paulo.

Cada consulta existe em 3 formatos:
- `linguagem-natural/` — como um gestor público perguntaria (sem códigos técnicos)
- `postgreSQL/` — query SQL com JOINs espaciais via PostGIS
- `neo4j-cypher/` — query Cypher com travessias no grafo de propriedades

## Como as consultas são analisadas

Além dos três eixos temáticos (educação, saúde e intersetorial), cada consulta é classificada por **tipo de operação dominante**. Essa classificação — registrada em [`grupos.json`](grupos.json) — é o que orienta o benchmark: os tempos de execução são agrupados por operação (e não por consulta individual), o que permite comparar, via boxplots, como cada modelo se comporta em filtros, agregações, anti-joins, travessias multi-hop e operações espaciais.

| Operação | Descrição | Nº de consultas |
|----------|-----------|-----------------|
| **filtro** | seleção/listagem por atributos, sem agregação/anti-join/distância | 12 |
| **agregacao** | `SUM`/`COUNT`/`AVG` ou estatística por território | 30 |
| **anti_join** | ausência/vazio de cobertura (`NOT EXISTS`, sem equipamento) | 8 |
| **multi_hop** | travessia lateral, auto-relação ou cruzamento educação × saúde | 10 |
| **espacial** | distância/raio/KNN (`point.distance` / `ST_DWithin`) | 6 |

## Níveis de agregação territorial

As consultas foram propositalmente distribuídas entre diferentes níveis de agregação territorial, para exercitar a hierarquia do grafo (`UF → Município → Distrito → Subdistrito → [Bairro] → SetorCensitário`) em diversas profundidades. Toda consulta que retorna um nível abaixo do município também retorna o município correspondente, para tornar o resultado autoexplicativo.

---

## Eixo 1 — Educação Básica (27 consultas)

Cruzamento entre variáveis de oferta escolar (turmas por etapa, dependência administrativa, infraestrutura) e indicadores de vulnerabilidade territorial.

| # | Nível | Operação | Pergunta |
|---|-------|----------|----------|
| Q01 | Município | agregacao | Quantas escolas de educação básica existem em cada município? |
| Q02 | Município | agregacao | Qual é a proporção de escolas públicas em relação às privadas em cada município? |
| Q03 | Lista | filtro | Quais escolas não possuem esgoto ligado à rede pública nem fossa séptica? |
| Q04 | Município | agregacao | Quantas escolas possuem quadra de esportes, seja coberta ou descoberta, em cada município? |
| Q05 | Lista | filtro | Quais escolas atendem simultaneamente turmas de Creche e turmas de Ensino Médio no mesmo estabelecimento? |
| Q06 | Setor | anti_join | Quais setores censitários possuem as maiores populações de adultos não alfabetizados e não contam com nenhuma escola instalada? |
| Q07 | Lista | filtro | Quais escolas públicas de Ensino Médio diurno estão localizadas em setores onde há presença de famílias indígenas responsáveis por domicílios? |
| Q08 | Distrito | agregacao | Quantas escolas de Educação Infantil oferecem turmas em tempo integral em distritos com alta concentração de famílias com estrutura estendida? |
| Q09 | Lista | filtro | Quais escolas de Ensino Fundamental estão em setores onde mais de 50 moradores residem em domicílios improvisados? |
| Q10 | Lista | multi_hop | Para cada escola que oferta Ensino Médio, quantas escolas de Ensino Fundamental existem no mesmo distrito? |
| Q11 | Lista | filtro | Quais escolas com Ensino Médio noturno estão em setores onde há jovens de 15 a 19 anos não alfabetizados, indicando demanda por EJA? |
| Q12 | Distrito | agregacao | Qual a razão entre turmas de creche e a população de crianças de 0 a 4 anos em cada distrito do estado? |
| Q13 | Lista | filtro | Quantos domicílios com mais de 5 moradores estão próximos de escolas que ofertam ensino EAD ou semipresencial? |
| Q14 | Lista | agregacao | Quais escolas privadas de Educação Infantil estão em distritos com alta população de crianças de 0 a 4 anos? |
| Q15 | Bairro | multi_hop | Quantas turmas de creche em tempo integral existem em bairros com alta presença de mulheres chefes de família sem cônjuge? |
| Q16 | Distrito | agregacao | Quais distritos têm os maiores vazios de Educação Especial Inclusiva frente ao volume de jovens de 15 a 19 anos? |
| Q17 | Setor | agregacao | Quantas escolas de Ensino Médio estão em setores onde predominam moradores em casas de vila ou condomínio? |
| Q18 | Município | agregacao | Qual a distribuição de turmas de EJA de Ensino Médio por município, confrontando com a população analfabeta de 15 a 19 anos? |
| Q19 | Subdistrito | agregacao | Quais subdistritos apresentam a maior disparidade na oferta de turmas de Educação Infantil entre seus setores? |
| Q20 | Distrito | agregacao | Qual a proporção de escolas com Educação Especial Inclusiva em cada distrito, frente à demanda de domicílios permanentes ocupados? |
| Q21 | Lista | filtro | Quais escolas públicas estaduais com turmas de EJA Fundamental estão em setores com presença expressiva de moradores em cortiços? |
| Q22 | Distrito | agregacao | Como se comporta a oferta de turmas de Ensino Básico diurno em distritos com alta concentração de população parda? |
| Q23 | Setor | agregacao | Quantas escolas da rede pública estão em setores onde os domicílios não possuem nenhum banheiro de uso exclusivo? |
| Q24 | Lista | multi_hop | Quais escolas sem laboratório de ciências estão em distritos onde pelo menos 5 outras escolas possuem laboratório de ciências? |
| Q25 | Lista | multi_hop | Quais escolas são a única opção de Ensino Médio em seu distrito? |
| Q26 | Lista | espacial | Quais escolas que não ofertam creche possuem alguma escola com creche num raio de 2 km? |
| Q27 | Lista | espacial | Quais escolas de Educação Infantil localizadas em setores com mais de 100 crianças de 0 a 4 anos estão a mais de 3 km de qualquer outra escola de Educação Infantil? |

---

## Eixo 2 — Saúde Pública e Privada (27 consultas)

Cruzamento entre variáveis de oferta assistencial (internação, ambulatório, urgência, vigilância, diagnose) por tipo de convênio e indicadores territoriais do Censo 2022.

| # | Nível | Operação | Pergunta |
|---|-------|----------|----------|
| Q01 | Município | agregacao | Quais municípios registram os maiores índices de domicílios improvisados e qual a oferta de leitos de internação pelo SUS nessas localidades? |
| Q02 | Lista | filtro | Quais unidades de saúde com atendimento ambulatorial pelo SUS estão em setores onde há jovens de 15 a 19 anos não alfabetizados? |
| Q03 | Setor | anti_join | Quais setores com mais de 1.000 moradores não possuem nenhum estabelecimento de saúde, configurando um vazio sanitário? |
| Q04 | Lista | filtro | Quais unidades de saúde com atendimento de urgência por plano privado estão em setores com alta população de crianças de 0 a 4 anos do sexo feminino? |
| Q05 | Setor | agregacao | Quantas unidades de saúde com atendimento de Vigilância em Saúde pelo SUS cobrem setores com alta presença de crianças de 0 a 9 anos moradoras de domicílios cujo esgotamento é por fossa rudimentar ou buraco? |
| Q06 | Setor | anti_join | Quais setores com alta população de idosos de 60 anos ou mais não possuem nenhuma unidade de Urgência pelo SUS? |
| Q07 | Distrito | agregacao | Qual o total de domicílios permanentes ocupados em distritos que contam com mais de 5 unidades de internação pelo SUS? |
| Q08 | Distrito | agregacao | Quais distritos de Campinas possuem internação por gratuidade em territórios com alta proporção de domicílios chefiados por mulheres sem cônjuge? |
| Q09 | Lista | filtro | Quais unidades de Vigilância em Saúde pelo SUS estão em territórios com alta concentração de idosos de 70 anos ou mais? |
| Q10 | Distrito | agregacao | Quais distritos com mais de 50.000 habitantes possuem menos de 3 ambulatórios pelo SUS? |
| Q11 | Lista | filtro | Quais unidades de Urgência pelo SUS estão em setores com alta densidade de população idosa de 60 anos ou mais? |
| Q12 | Distrito | agregacao | Quantos centros de Diagnose e Terapia pelo SUS existem em distritos com alta população autodeclarada preta? |
| Q13 | Lista | filtro | Quais unidades de internação por plano privado estão em setores com alto adensamento vertical de apartamentos (pelo menos 100 moradores desses domicílios)? |
| Q14 | Setor | agregacao | Quais setores sem abastecimento de água pela rede geral possuem atendimento ambulatorial por plano público? |
| Q15 | Bairro | agregacao | Quantas unidades de Urgência particular privada estão em bairros com maior presença de responsáveis de domicílio de raça amarela? |
| Q16 | Distrito | agregacao | Qual a proporção de domicílios em esgotamento sanitário precário por fossa rudimentar frente à população de cada distrito do estado? |
| Q17 | Setor | agregacao | Quantas unidades de Urgência por plano público cobrem setores com presença expressiva de população parda? |
| Q18 | Distrito | agregacao | Quais distritos têm domicílios sem banheiro de uso exclusivo e qual a presença de postos de Vigilância em Saúde pelo SUS nesses locais? |
| Q19 | Distrito | agregacao | Quantas unidades de urgência do SUS existem no distrito da Vila Sônia e qual a população total dessa área? |
| Q20 | Lista | multi_hop | Para cada unidade de internação pelo SUS, quantas unidades de atendimento ambulatorial pelo SUS existem no mesmo distrito? |
| Q21 | Município | agregacao | Qual a distribuição de postos de Vigilância em Saúde por plano público em cada município, confrontando com a população analfabeta adulta de 15 anos ou mais? |
| Q22 | Subdistrito | agregacao | Quais subdistritos registram a maior disparidade na oferta de leitos de internação pelo SUS entre seus setores? |
| Q23 | Distrito | agregacao | Como se comporta a oferta de leitos de internação com gratuidade em distritos com alta concentração de população de raça amarela de 60 anos ou mais? |
| Q24 | Setor | agregacao | Quantas unidades de Vigilância em Saúde do SUS estão em setores com esgotamento sanitário inexistente? |
| Q25 | Município | agregacao | Quantas pessoas em setores rurais contam com suporte de atendimento ambulatorial pelo SUS? |
| Q26 | Lista | espacial | Para cada unidade de Diagnose e Terapia pelo SUS, qual a distância até a unidade de Urgência pelo SUS mais próxima? |
| Q27 | Lista | espacial | Quais unidades de Urgência pelo SUS localizadas em setores com mais de 80 pessoas responsáveis por domicílio com 60 anos ou mais estão a mais de 10 km de qualquer outra unidade de Urgência pelo SUS? |

---

## Eixo 3 — Intersetorial (12 consultas)

Cruzamento simultâneo entre equipamentos de educação e saúde no mesmo território,
mesclando as três fontes (IBGE, INEP e CNES) para identificar vazios, desbalanceamentos e coberturas complementares.

| # | Nível | Operação | Pergunta |
|---|-------|----------|----------|
| Q01 | Setor | anti_join | Quais setores possuem pelo menos uma escola pública mas nenhum estabelecimento de saúde com atendimento ambulatorial pelo SUS? |
| Q02 | Setor | anti_join | Quais setores com alta vulnerabilidade habitacional (pelo menos 100 moradores em domicílios improvisados) não possuem nenhum equipamento público, nem escola nem unidade de saúde? |
| Q03 | Distrito | multi_hop | Quais distritos com muitos domicílios em vias sem pavimentação e sem calçada concentram escolas públicas de Ensino Fundamental, mas oferecem menos de 3 unidades de Urgência pelo SUS? |
| Q04 | Bairro | anti_join | Quais bairros possuem creches mas não possuem nenhuma unidade de saúde ambulatorial pelo SUS? |
| Q05 | Município | multi_hop | Qual a razão entre o número de escolas públicas e o número de unidades de saúde ambulatorial pelo SUS por município, confrontada com a população de idosos de 60 anos ou mais de cada um? |
| Q06 | Setor | anti_join | Quais setores com alta concentração de idosos possuem escola com EJA mas não possuem nenhuma unidade de Urgência pelo SUS? |
| Q07 | Setor | anti_join | Quais setores com escola que oferta EJA e muitos domicílios sem iluminação pública no entorno não possuem nenhuma unidade de Urgência pelo SUS? |
| Q08 | Distrito | multi_hop | Quais distritos com crianças em domicílios improvisados possuem cobertura simultânea de creches e internação pelo SUS? |
| Q09 | Setor | multi_hop | Qual o total de equipamentos públicos por setor nos territórios com mais de 1.000 habitantes, identificando os mais desassistidos? |
| Q10 | Distrito | multi_hop | Em cada distrito do estado, qual a presença de responsáveis indígenas por domicílio, de escolas públicas de Ensino Fundamental e de unidades de Vigilância em Saúde pelo SUS? |
| Q11 | Lista | espacial | Quais escolas estão a mais de 5 km da unidade de Vigilância em Saúde pelo SUS mais próxima? |
| Q12 | Lista | espacial | Quais escolas públicas localizadas em setores com mais de 30 domicílios que jogam lixo em terreno baldio, encosta ou área pública estão a mais de 4 km de qualquer unidade de Vigilância em Saúde pelo SUS? |