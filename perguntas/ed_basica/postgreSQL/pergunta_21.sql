SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    m.co_entidade AS id_escola,
    m.no_entidade AS nome_escola,
    m.qt_tur_eja_fund AS turmas_eja_fundamental,
    COALESCE(ascdp.v00050, 0) AS moradores_cortico
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, eq._geom)
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte1 ascdp
  ON s.cd_setor = ascdp.cd_setor
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
  AND m.tp_dependencia = '2'
  AND m.qt_tur_eja_fund > 0
  AND COALESCE(ascdp.v00050, 0) > 0
ORDER BY moradores_cortico DESC;
