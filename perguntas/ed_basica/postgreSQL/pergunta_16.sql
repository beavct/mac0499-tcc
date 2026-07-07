SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    SUM(COALESCE(demo.v01012, 0) + COALESCE(demo.v01025, 0)) AS total_jovens_15_19,
    COUNT(DISTINCT CASE WHEN m.qt_tur_esp_cc > 0 THEN m.co_entidade END) AS escolas_com_inclusiva
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_demografia demo 
  ON s.cd_setor = demo.cd_setor
LEFT JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
  ON ST_Contains(s._geom, eq._geom)
LEFT JOIN culturaeduca.datasets.microdados_ed_basica_2024 m 
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
GROUP BY s.nm_mun, s.nm_dist
ORDER BY escolas_com_inclusiva ASC, total_jovens_15_19 DESC;