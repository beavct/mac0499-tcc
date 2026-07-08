SELECT DISTINCT
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    COALESCE(carac.v00006, 0) AS moradores_improvisados
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte1 carac
  ON s.cd_setor = carac.cd_setor
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
  ON ST_Contains(s._geom, eq._geom)
JOIN culturaeduca.datasets.microdados_ed_basica_2024 m
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
WHERE m.tp_dependencia IN ('1', '2', '3')
  AND COALESCE(carac.v00006, 0) > 0
  AND NOT EXISTS (
      SELECT 1
      FROM culturaeduca.datasets.eq_saude_2025 saude
      JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
        ON saude.co_unidade = a.co_unidade AND a.at_02_conv_01 = '1'
      WHERE ST_Contains(s._geom, saude._geom)
  )
ORDER BY moradores_improvisados DESC;
