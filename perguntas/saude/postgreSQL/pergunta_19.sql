SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    SUM(COALESCE(b.v0001, 0)) AS populacao_total,
    COUNT(DISTINCT saude.co_unidade) AS unidades_internacao_publicas
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_basico b 
  ON s.cd_setor = b.cd_setor
LEFT JOIN culturaeduca.datasets.eq_saude_2025 saude 
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade AND a.at_01_conv_05 = '1'
WHERE s.nm_dist = 'Vila Sônia'
GROUP BY s.nm_mun, s.nm_dist;
