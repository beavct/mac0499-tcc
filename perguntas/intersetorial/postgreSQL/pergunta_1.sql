SELECT
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    COUNT(DISTINCT m.co_entidade) AS escolas_publicas
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
  ON ST_Contains(s._geom, eq._geom)
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
  AND m.tp_dependencia IN ('1', '2', '3')
  AND NOT EXISTS (
    SELECT 1 FROM culturaeduca.datasets.eq_saude_2025 saude
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON saude.co_unidade = a.co_unidade
    WHERE ST_Contains(s._geom, saude._geom)
      AND a.at_02_conv_01 = '1'
  )
GROUP BY s.nm_mun, s.nm_dist, s.cd_setor
ORDER BY escolas_publicas DESC;