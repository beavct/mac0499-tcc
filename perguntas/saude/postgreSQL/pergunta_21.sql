SELECT
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    SUM(COALESCE(alf.v00901, 0)) AS analfabetos_15_mais,
    COUNT(DISTINCT a.co_unidade) AS unidades_vigilancia_publica
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_alfabetizacao alf
  ON s.cd_setor = alf.cd_setor
LEFT JOIN culturaeduca.datasets.eq_saude_2025 saude
  ON ST_Contains(s._geom, saude._geom)
LEFT JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade AND a.at_06_conv_05 = '1'
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
GROUP BY s.nm_mun, s.nm_dist
ORDER BY analfabetos_15_mais DESC;
