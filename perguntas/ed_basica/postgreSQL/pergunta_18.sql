SELECT 
    s.nm_mun AS municipio,
    SUM(COALESCE(alf.v00644, 0)) AS total_jovens_15_19_analfabetos,
    SUM(m.qt_tur_eja_med) AS total_turmas_eja
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, eq._geom)
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_alfabetizacao alf 
  ON s.cd_setor = alf.cd_setor
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
GROUP BY s.nm_mun
ORDER BY total_jovens_15_19_analfabetos DESC;