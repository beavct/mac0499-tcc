SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    m.co_entidade AS id_escola,
    m.no_entidade AS nome_escola,
    SUM(COALESCE(demo.v01020, 0) + COALESCE(demo.v01009, 0)) AS populacao_infantil_distrito
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, eq._geom)
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_demografia demo 
  ON s.cd_setor = demo.cd_setor
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
  AND m.tp_dependencia = '4'
  AND m.qt_tur_inf > 0
GROUP BY s.nm_mun, s.nm_dist, m.co_entidade, m.no_entidade
ORDER BY populacao_infantil_distrito DESC;