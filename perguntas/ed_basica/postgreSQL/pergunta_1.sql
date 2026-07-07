SELECT
    s.nm_mun AS municipio,
    COUNT(DISTINCT eq.co_entidade) AS total_escolas
FROM culturaeduca.datasets.eq_educacao_basica_2024 eq
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
  ON ST_Contains(s._geom, eq._geom)
GROUP BY s.nm_mun
ORDER BY s.nm_mun, total_escolas DESC;
