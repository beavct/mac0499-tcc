SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    MAX(m.qt_tur_inf) - MIN(m.qt_tur_inf) AS disparidade_oferta_infantil
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, eq._geom)
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
GROUP BY s.nm_mun, s.nm_dist
ORDER BY disparidade_oferta_infantil DESC;