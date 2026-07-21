-- Vizinho mais próximo: para cada unidade de Diagnose e Terapia (SADT) SUS,
-- a unidade de Urgência SUS mais próxima e a distância até ela.
--
-- Nota de comparação com o Neo4j: 4 unidades SADT do estado (em Lorena, Mongaguá,
-- Monteiro Lobato e Santa Fé do Sul) têm coordenadas do CNES que não caem dentro
-- de nenhum polígono de setor censitário (ST_Contains). Como o ETL associa cada
-- equipamento ao setor que o contém, essas 4 não são carregadas como nós no grafo.
-- Elas aparecem nesta consulta no PostgreSQL (que mede distância entre pontos, sem
-- depender do setor), mas não no Cypher — o que explica a pequena diferença de
-- linhas entre os dois. A origem é a qualidade da coordenada na fonte, não a query.
SELECT
    diag.co_unidade AS id_diagnose,
    diag.no_fantasia AS nome_diagnose,
    prox.co_unidade AS id_urgencia_proxima,
    prox.no_fantasia AS nome_urgencia_proxima,
    ROUND(ST_Distance(diag._geog, prox._geog)::numeric, 1) AS distancia_m
FROM culturaeduca.datasets.eq_saude_2025 diag
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos adiag
  ON adiag.co_unidade = diag.co_unidade AND adiag.at_03_conv_01 = '1'
CROSS JOIN LATERAL (
    SELECT urg.co_unidade, urg.no_fantasia, urg._geog
    FROM culturaeduca.datasets.eq_saude_2025 urg
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos aurg
      ON aurg.co_unidade = urg.co_unidade AND aurg.at_04_conv_01 = '1'
    WHERE urg.co_unidade <> diag.co_unidade
    ORDER BY diag._geog <-> urg._geog
    LIMIT 1
) prox
ORDER BY distancia_m DESC;
