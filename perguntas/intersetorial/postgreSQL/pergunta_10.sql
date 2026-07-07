SELECT
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    COALESCE(dom2.v00094, 0) AS responsaveis_indigenas,
    COUNT(DISTINCT m.co_entidade) AS escolas_fund_publicas,
    COUNT(DISTINCT saude.co_unidade) AS saude_outros_sus
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte2 dom2
  ON s.cd_setor = dom2.cd_setor
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq ON ST_Contains(s._geom, eq._geom)
JOIN culturaeduca.datasets.microdados_ed_basica_2024 m
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.eq_saude_2025 saude ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade
WHERE COALESCE(dom2.v00094, 0) > 0
  AND m.tp_dependencia IN ('1', '2', '3')
  AND (m.qt_tur_fund_ai > 0 OR m.qt_tur_fund_af > 0)
  AND a.at_05_conv_01 = '1'
GROUP BY s.nm_mun, s.nm_dist, s.cd_setor, dom2.v00094
ORDER BY responsaveis_indigenas DESC;