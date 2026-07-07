SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    SUM(COALESCE(raca.v01320, 0)) AS populacao_parda,
    COUNT(DISTINCT saude.co_unidade) AS urgencias_publicas
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_raca_cor raca 
  ON s.cd_setor = raca.cd_setor
LEFT JOIN culturaeduca.datasets.eq_saude_2025 saude 
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade AND a.at_03_conv_05 = '1'
GROUP BY s.nm_mun, s.nm_dist, s.cd_setor
ORDER BY populacao_parda DESC;
