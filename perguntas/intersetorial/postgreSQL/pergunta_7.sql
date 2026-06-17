SELECT
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    m.co_entidade AS id_escola,
    m.no_entidade AS nome_escola,
    saude.co_unidade AS id_saude,
    saude.no_fantasia AS nome_saude
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
  ON ST_Contains(s._geom, eq._geom)
JOIN culturaeduca.datasets.eq_saude_2025 saude
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
  AND m.in_esgoto_rede_publica = '0'
  AND m.in_esgoto_fossa = '0'
  AND a.at_06_conv_01 = '1'
ORDER BY s.nm_mun, s.nm_dist;