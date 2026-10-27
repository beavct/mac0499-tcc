-- Vizinho mais próximo: para cada unidade de Diagnose e Terapia (SADT) SUS,
-- a unidade de Urgência SUS mais próxima e a distância até ela.
--
-- Nota de comparação com o Neo4j: 4 unidades SADT do estado têm coordenadas do CNES que não
-- caem em nenhum setor censitário e não são carregadas no grafo; o JOIN com os setores
-- (ST_Contains, como no ETL) as exclui também aqui. A unidade de Urgência mais próxima ainda
-- difere em cerca de 130 casos, porque aqui a distância é geodésica e o point.distance do
-- Neo4j usa a fórmula de haversine (nenhuma unidade de Urgência SUS fica fora dos setores).
SELECT
    s.nm_mun AS municipio,
    diag.co_unidade AS id_diagnose,
    diag.no_fantasia AS nome_diagnose,
    prox.co_unidade AS id_urgencia_proxima,
    prox.no_fantasia AS nome_urgencia_proxima,
    ROUND(ST_Distance(diag._geog, prox._geog)::numeric, 1) AS distancia_m
FROM culturaeduca.datasets.eq_saude_2025 diag
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos adiag
  ON adiag.co_unidade = diag.co_unidade AND adiag.at_03_conv_01 = '1'
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
  ON ST_Contains(s._geom, diag._geom)
CROSS JOIN LATERAL (
    SELECT urg.co_unidade, urg.no_fantasia, urg._geog
    FROM culturaeduca.datasets.eq_saude_2025 urg
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos aurg
      ON aurg.co_unidade = urg.co_unidade AND aurg.at_04_conv_01 = '1'
    WHERE urg.co_unidade <> diag.co_unidade
    ORDER BY diag._geog <-> urg._geog
    LIMIT 1
) prox;
