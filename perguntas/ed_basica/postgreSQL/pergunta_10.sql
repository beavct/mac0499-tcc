SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    m.co_entidade AS id_escola,
    m.no_entidade AS nome_escola,
    m.qt_tur_esp_ce AS turmas_especial_exclusiva,
    COALESCE(ascdp.v00050, 0) AS moradores_cortico
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, eq._geom)
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte1 ascdp
  ON s.cd_setor = ascdp.cd_setor
WHERE m.qt_tur_esp_ce > 0
  AND COALESCE(ascdp.v00050, 0) > 0
ORDER BY moradores_cortico DESC;