SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    COUNT(DISTINCT saude.co_unidade) AS vigilancia_saude_sus
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte2 dom2 
  ON s.cd_setor = dom2.cd_setor
LEFT JOIN culturaeduca.datasets.eq_saude_2025 saude 
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade AND a.at_06_conv_01 = '1'
WHERE COALESCE(dom2.v00486, 0) = 0
GROUP BY s.nm_mun, s.nm_dist;
