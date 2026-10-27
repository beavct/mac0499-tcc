# Perguntas — as 66 consultas do benchmark

Esta pasta guarda as **66 consultas** socioespaciais usadas no trabalho: no benchmark entre o modelo relacional (PostgreSQL/PostGIS) e o modelo em grafos (Neo4j), e como gabarito da avaliação do Text-to-Cypher. As consultas cruzam os microdados de equipamentos públicos (INEP 2024 e CNES 2025) com os agregados do Censo 2022 do IBGE, sobre todo o estado de São Paulo.

Cada consulta existe em três formatos, um por pasta dentro de cada eixo:

- `linguagem-natural/`: a pergunta como um gestor público a faria, sem códigos técnicos;
- `postgreSQL/`: a consulta SQL, com as junções espaciais do PostGIS;
- `neo4j-cypher/`: a consulta Cypher, com as travessias no grafo.

As duas versões de cada consulta devolvem o mesmo resultado, o que é conferido pelo script de [`../testes/validacao/`](../testes/validacao).

## Tipos de operação

Além dos três eixos temáticos (educação, saúde e intersetorial), cada consulta é classificada pelo tipo de operação que predomina nela. A classificação fica em [`grupos.json`](grupos.json) e orienta o benchmark: os tempos são agrupados por operação, o que permite comparar como cada banco se comporta em filtros, agregações, ausências de vínculo, travessias e operações espaciais.

| Operação | Descrição | Consultas |
|----------|-----------|----------:|
| `filtro` | seleção ou listagem por atributos, sem agregação, ausência ou distância | 12 |
| `agregacao` | `SUM`, `COUNT`, `AVG` ou outra estatística por território | 30 |
| `anti_join` | ausência de cobertura (`NOT EXISTS`, nenhum equipamento) | 8 |
| `multi_hop` | travessia lateral, autorrelação ou cruzamento entre educação e saúde | 10 |
| `espacial` | distância, raio ou vizinho mais próximo (`point.distance` / `ST_DWithin`) | 6 |

## Dificuldade

Cada consulta Cypher também tem um nível de dificuldade (fácil, média, difícil ou extra), usado para avaliar o Text-to-Cypher por nível. O critério é o do Spider, que conta os componentes de cada consulta, adaptado ao Cypher e a este conjunto. Os níveis ficam em [`dificuldade.json`](dificuldade.json), gerado por:

```bash
cd perguntas
python classificar_dificuldade.py
```

| Nível | Quant. de Consultas |
|-------|----------:|
| fácil | 5 |
| média | 22 |
| difícil | 28 |
| extra | 11 |

## Níveis de agregação territorial

As consultas estão distribuídas entre vários níveis da hierarquia territorial (`UF → Município → Distrito → Subdistrito → [Bairro] → SetorCensitario`), para exercitar o grafo em profundidades diferentes. Toda consulta que devolve um nível abaixo do município também devolve o município correspondente, para que o resultado se explique sozinho.

---

## Eixo 1 — Educação Básica (27 consultas)

Cruzamento entre variáveis de oferta escolar (turmas por etapa, dependência administrativa, infraestrutura) e indicadores de vulnerabilidade territorial.

| # | Nível | Operação | Pergunta |
|---|-------|----------|----------|
| Q01 | Município | agregacao | Quantas escolas de educação básica existem em cada município? |
| Q02 | Município | agregacao | Quantas escolas de cada dependência administrativa (federal, estadual, municipal e privada) há em cada município, e qual o percentual de cada uma no total de escolas do município? |
| Q03 | Lista | filtro | Quais escolas não possuem esgoto ligado à rede pública nem fossa séptica? |
| Q04 | Município | agregacao | Quantas escolas possuem quadra de esportes, seja coberta ou descoberta, em cada município? |
| Q05 | Lista | filtro | Quais escolas atendem simultaneamente turmas de Creche e turmas de Ensino Médio no mesmo estabelecimento? |
| Q06 | Setor | anti_join | Quais são os 20 setores censitários com as maiores populações de pessoas de 15 anos ou mais não alfabetizadas que não contam com nenhuma escola instalada? |
| Q07 | Lista | filtro | Quais escolas públicas (federais, estaduais ou municipais) que ofertam Ensino Médio e têm turmas no turno diurno estão localizadas em setores com pelo menos um domicílio do tipo casa com responsável indígena? |
| Q08 | Distrito | agregacao | Quantas escolas de Educação Infantil oferecem turmas em tempo integral em cada distrito, ordenados pelo número de famílias com estrutura estendida, do maior para o menor? |
| Q09 | Lista | filtro | Quais escolas de Ensino Fundamental estão em setores onde mais de 50 moradores residem em domicílios improvisados? |
| Q10 | Lista | multi_hop | Para cada escola que oferta Ensino Médio, quantas escolas de Ensino Fundamental existem no mesmo distrito? |
| Q11 | Lista | filtro | Quais escolas que ofertam Ensino Médio e têm turmas no turno noturno estão em setores onde há jovens de 15 a 19 anos não alfabetizados, indicando demanda por EJA? |
| Q12 | Distrito | agregacao | Qual a razão entre turmas de creche e a população de crianças de 0 a 4 anos em cada distrito do estado, expressa em turmas por 100 crianças? |
| Q13 | Lista | filtro | Para cada escola que oferta turmas semipresenciais ou EAD, quantos domicílios com 5 moradores há no setor censitário onde ela está? |
| Q14 | Lista | agregacao | Quais escolas privadas de Educação Infantil existem em cada distrito, ordenadas pela população de crianças de 0 a 4 anos do distrito, da maior para a menor? |
| Q15 | Bairro | multi_hop | Quantas turmas de creche em tempo integral existem em cada bairro, ordenados pelo número de mulheres que moram sozinhas, do maior para o menor? |
| Q16 | Distrito | agregacao | Quais distritos têm os maiores vazios de Educação Especial Inclusiva frente ao volume de jovens de 15 a 19 anos, ordenados do menor para o maior número de escolas com Educação Especial Inclusiva e, em caso de empate, do maior para o menor número de jovens? |
| Q17 | Setor | agregacao | Em cada setor censitário com escolas de Ensino Médio, quantas são essas escolas e quantos moradores em casas de vila ou condomínio há no setor? |
| Q18 | Município | agregacao | Qual a distribuição de turmas de EJA de Ensino Médio por município, confrontando com a população analfabeta de 15 a 19 anos? |
| Q19 | Subdistrito | agregacao | Quais subdistritos apresentam a maior disparidade na oferta de turmas de Educação Infantil entre as suas escolas (a diferença entre a escola com mais e a com menos turmas), ordenados da maior para a menor disparidade? |
| Q20 | Distrito | agregacao | Em cada distrito, quantas escolas há, quantas oferecem Educação Especial Inclusiva e quantos domicílios particulares permanentes ocupados existem? |
| Q21 | Lista | filtro | Quais escolas públicas estaduais com turmas de EJA Fundamental estão em setores com domicílios em cortiços? |
| Q22 | Distrito | agregacao | Quantas turmas da Educação Básica no turno diurno há em cada distrito, ordenados pela população parda, da maior para a menor? |
| Q23 | Setor | agregacao | Em quais setores com pelo menos um domicílio sem banheiro de uso exclusivo há escolas da rede pública (federal, estadual ou municipal), e quantas são em cada setor? |
| Q24 | Lista | multi_hop | Quais escolas sem laboratório de ciências estão em distritos onde pelo menos 5 outras escolas possuem laboratório de ciências? |
| Q25 | Lista | multi_hop | Quais escolas são a única opção de Ensino Médio em seu distrito? |
| Q26 | Lista | espacial | Quais escolas que não ofertam creche possuem alguma escola com creche num raio de 2 km? |
| Q27 | Lista | espacial | Quais escolas de Educação Infantil localizadas em setores com mais de 100 crianças de 0 a 4 anos estão a mais de 3 km de qualquer outra escola de Educação Infantil? |

---

## Eixo 2 — Saúde Pública e Privada (27 consultas)

Cruzamento entre variáveis de oferta assistencial (internação, ambulatório, urgência, vigilância, diagnose) por tipo de convênio e indicadores territoriais do Censo 2022.

| # | Nível | Operação | Pergunta |
|---|-------|----------|----------|
| Q01 | Município | agregacao | Quantos domicílios improvisados e quantas unidades de internação pelo SUS há em cada município, ordenados do maior para o menor número de domicílios improvisados? |
| Q02 | Lista | filtro | Quais unidades de saúde com atendimento ambulatorial pelo SUS estão em setores onde há jovens de 15 a 19 anos não alfabetizados? |
| Q03 | Setor | anti_join | Quais setores com mais de 1.000 moradores não possuem nenhum estabelecimento de saúde, configurando um vazio sanitário? |
| Q04 | Lista | filtro | Quais unidades de saúde com atendimento de Urgência por plano privado estão em setores com pelo menos uma criança do sexo feminino de 0 a 4 anos? |
| Q05 | Setor | agregacao | Em quais setores com pelo menos uma criança de 0 a 9 anos morando em domicílio cujo esgoto do banheiro ou sanitário vai para fossa rudimentar ou buraco há unidades de saúde com atendimento de Vigilância em Saúde pelo SUS, e quantas são em cada setor? |
| Q06 | Setor | anti_join | Quais setores com mais de 50 idosos de 60 anos ou mais não possuem nenhuma unidade de Urgência pelo SUS? |
| Q07 | Distrito | agregacao | Qual o total de domicílios permanentes ocupados em distritos que contam com mais de 5 unidades de internação pelo SUS? |
| Q08 | Distrito | agregacao | Quantos estabelecimentos com internação por gratuidade há em cada distrito de Campinas, ordenados pelo número de domicílios chefiados por mulheres sem cônjuge, do maior para o menor? |
| Q09 | Lista | filtro | Quais unidades de Vigilância em Saúde pelo SUS estão em setores com pelo menos um idoso de 70 anos ou mais? |
| Q10 | Distrito | agregacao | Quais distritos com mais de 50.000 habitantes possuem menos de 3 ambulatórios pelo SUS? |
| Q11 | Lista | filtro | Quais unidades de Urgência pelo SUS estão em setores com pelo menos uma pessoa idosa de 60 anos ou mais? |
| Q12 | Distrito | agregacao | Quantos centros de Diagnose e Terapia pelo SUS existem em cada distrito, ordenados pela população autodeclarada preta, da maior para a menor? |
| Q13 | Lista | filtro | Quais unidades de internação por plano privado estão em setores com alto adensamento vertical de apartamentos, ou seja, mais de 100 moradores destes domicílios? |
| Q14 | Setor | agregacao | Quais setores sem abastecimento de água pela rede geral possuem atendimento ambulatorial por plano público? |
| Q15 | Bairro | agregacao | Quantas unidades de Urgência por plano de saúde privado há em cada bairro, ordenados pelo número de domicílios do tipo casa com responsável de raça amarela, do maior para o menor? |
| Q16 | Distrito | agregacao | Qual a proporção de domicílios com esgotamento sanitário precário por fossa rudimentar ou buraco, por mil habitantes, em cada distrito do estado? |
| Q17 | Setor | agregacao | Em quais setores há unidades de Urgência por plano público e quantas são em cada um, ordenados pela população parda do setor, da maior para a menor? |
| Q18 | Distrito | agregacao | Em cada distrito, quantos postos de Vigilância em Saúde pelo SUS estão em setores com domicílios sem banheiro nem sanitário? |
| Q19 | Distrito | agregacao | Quantas unidades de urgência do SUS existem no distrito da Vila Sônia e qual a população total dessa área? |
| Q20 | Lista | multi_hop | Para cada unidade de internação pelo SUS, quantas unidades de atendimento ambulatorial pelo SUS existem no mesmo distrito? |
| Q21 | Município | agregacao | Qual a distribuição de postos de Vigilância em Saúde por plano público em cada município, confrontando com a população analfabeta adulta de 15 anos ou mais? |
| Q22 | Subdistrito | agregacao | Quais subdistritos registram a maior disparidade na oferta de unidades de internação pelo SUS entre seus setores, ordenados da maior para a menor disparidade? |
| Q23 | Distrito | agregacao | Quantas unidades de internação com gratuidade há em cada distrito, ordenados pela população de raça amarela de 60 anos ou mais, da maior para a menor? |
| Q24 | Setor | agregacao | Em quais setores com pelo menos um domicílio sem esgotamento sanitário (por não ter banheiro nem sanitário) há unidades de Vigilância em Saúde do SUS, e quantas são em cada setor? |
| Q25 | Município | agregacao | Em cada município, quantas pessoas vivem em setores rurais que têm pelo menos uma unidade com atendimento ambulatorial pelo SUS? |
| Q26 | Lista | espacial | Para cada unidade de Diagnose e Terapia pelo SUS, qual a distância até a unidade de Urgência pelo SUS mais próxima? |
| Q27 | Lista | espacial | Quais unidades de Urgência pelo SUS localizadas em setores com mais de 80 pessoas responsáveis por domicílio com 60 anos ou mais estão a mais de 10 km de qualquer outra unidade de Urgência pelo SUS? |

---

## Eixo 3 — Intersetorial (12 consultas)

Cruzamento simultâneo entre equipamentos de educação e saúde no mesmo território, mesclando as três fontes (IBGE, INEP e CNES) para identificar vazios, desbalanceamentos e coberturas complementares.

| # | Nível | Operação | Pergunta |
|---|-------|----------|----------|
| Q01 | Setor | anti_join | Quais setores possuem pelo menos uma escola pública (federal, estadual ou municipal) mas nenhum estabelecimento de saúde com atendimento ambulatorial pelo SUS? |
| Q02 | Setor | anti_join | Quais setores com alta vulnerabilidade habitacional, ou seja, com mais de 100 moradores de domicílios improvisados, não possuem nenhum equipamento público, nem escola nem unidade de saúde? |
| Q03 | Distrito | multi_hop | Quais distritos com mais de 1.000 domicílios em vias sem pavimentação e mais de 1.000 domicílios em vias sem calçada têm mais de 5 escolas públicas (federais, estaduais ou municipais) com turmas de Ensino Fundamental, mas menos de 3 unidades de Urgência pelo SUS? |
| Q04 | Bairro | anti_join | Quais bairros possuem creches mas não possuem nenhuma unidade de saúde ambulatorial pelo SUS? |
| Q05 | Município | multi_hop | Qual a razão entre o número de escolas públicas (federais, estaduais ou municipais) e o número de unidades de saúde ambulatorial pelo SUS por município, confrontada com a população de idosos de 60 anos ou mais de cada um? |
| Q06 | Setor | anti_join | Quais setores com mais de 100 pessoas de 70 anos ou mais possuem escola com EJA mas não possuem nenhuma unidade de Urgência pelo SUS? |
| Q07 | Setor | anti_join | Quais setores com escola que oferta EJA e com mais de 30 domicílios sem iluminação pública no entorno não possuem nenhuma unidade de Urgência pelo SUS? |
| Q08 | Distrito | multi_hop | Nos distritos com crianças de 0 a 9 anos em domicílios improvisados, quantas escolas com turmas de creche e quantas unidades de internação pelo SUS existem? |
| Q09 | Setor | multi_hop | Qual o total de equipamentos (escolas e estabelecimentos de saúde, de qualquer rede) por setor nos setores com mais de 1.000 habitantes, identificando os 30 setores mais desassistidos (com menos equipamentos e, em caso de empate, mais habitantes)? |
| Q10 | Distrito | multi_hop | Em cada distrito do estado, quantos domicílios do tipo casa com responsável indígena, quantas escolas públicas (federais, estaduais ou municipais) com turmas de Ensino Fundamental (anos iniciais ou finais) e quantas unidades de Vigilância em Saúde pelo SUS existem? |
| Q11 | Lista | espacial | Quais escolas estão a mais de 5 km da unidade de Vigilância em Saúde pelo SUS mais próxima? |
| Q12 | Lista | espacial | Quais escolas públicas (federais, estaduais ou municipais) localizadas em setores com mais de 30 domicílios que jogam lixo em terreno baldio, encosta ou área pública estão a mais de 4 km de qualquer unidade de Vigilância em Saúde pelo SUS? |

---

## Referências

- Yu et al., *Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task*, EMNLP 2018 (critério de dificuldade)
