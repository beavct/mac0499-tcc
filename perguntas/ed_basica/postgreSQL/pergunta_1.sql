SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    COUNT(DISTINCT eq.co_entidade) AS total_escolas
FROM culturaeduca.datasets.eq_educacao_basica_2024 eq
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, eq._geom)
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
GROUP BY s.nm_mun, s.nm_dist
ORDER BY s.nm_mun, total_escolas DESC;