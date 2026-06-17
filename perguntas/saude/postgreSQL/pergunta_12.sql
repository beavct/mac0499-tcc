SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    SUM(COALESCE(raca.v01318, 0)) AS populacao_negra,
    COUNT(DISTINCT saude.co_unidade) AS centros_diagnose_sus
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_raca_cor raca 
  ON s.cd_setor = raca.cd_setor
LEFT JOIN culturaeduca.datasets.eq_saude_2025 saude 
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade AND a.at_07_conv_01 = '1'
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
GROUP BY s.nm_mun, s.nm_dist
ORDER BY populacao_negra DESC;
