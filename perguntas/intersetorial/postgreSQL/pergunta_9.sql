SELECT
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    COALESCE(b.v0001, 0) AS populacao,
    COUNT(DISTINCT eq.co_entidade) AS qtd_escolas,
    COUNT(DISTINCT saude.co_unidade) AS qtd_saude,
    (COUNT(DISTINCT eq.co_entidade) + COUNT(DISTINCT saude.co_unidade)) AS total_equipamentos
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_basico b ON s.cd_setor = b.cd_setor
LEFT JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq ON ST_Contains(s._geom, eq._geom)
LEFT JOIN culturaeduca.datasets.eq_saude_2025 saude ON ST_Contains(s._geom, saude._geom)
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
  AND COALESCE(b.v0001, 0) > 1000
GROUP BY s.nm_mun, s.nm_dist, s.cd_setor, b.v0001
ORDER BY total_equipamentos ASC, populacao DESC
LIMIT 30;