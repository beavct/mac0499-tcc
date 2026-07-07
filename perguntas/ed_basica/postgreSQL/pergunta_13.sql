SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    m.co_entidade AS id_escola,
    m.no_entidade AS nome_escola,
    m.qt_tur_bas_ead AS turmas_ead,
    COALESCE(ascdp.v00078, 0) AS domicilios_mais_5_moradores
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, eq._geom)
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte1 ascdp
  ON s.cd_setor = ascdp.cd_setor
WHERE m.qt_tur_bas_ead > 0
ORDER BY domicilios_mais_5_moradores DESC;