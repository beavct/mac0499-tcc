SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    m.co_entidade AS id_escola,
    m.no_entidade AS nome_escola,
    (COALESCE(alf.v00644, 0) - COALESCE(alf.v00748, 0)) AS jovens_15_19_analfabetos
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, eq._geom)
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_alfabetizacao alf 
  ON s.cd_setor = alf.cd_setor
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
  AND m.qt_tur_med > 0
  AND m.qt_tur_bas_n > 0
  AND (COALESCE(alf.v00644, 0) - COALESCE(alf.v00748, 0)) > 0
ORDER BY jovens_15_19_analfabetos DESC;
