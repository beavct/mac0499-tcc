SELECT
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    COUNT(DISTINCT eq.co_entidade) AS total_escolas,
    COUNT(DISTINCT a.co_unidade) AS total_saude_sus,
    ROUND(COUNT(DISTINCT eq.co_entidade)::numeric / NULLIF(COUNT(DISTINCT a.co_unidade), 0), 2) AS razao_escola_saude
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
LEFT JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
  ON ST_Contains(s._geom, eq._geom)
LEFT JOIN culturaeduca.datasets.eq_saude_2025 saude
  ON ST_Contains(s._geom, saude._geom)
LEFT JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade AND a.at_02_conv_01 = '1'
GROUP BY s.nm_mun, s.nm_dist
HAVING COUNT(DISTINCT eq.co_entidade) > 10 AND COUNT(DISTINCT a.co_unidade) < 3
ORDER BY razao_escola_saude DESC;