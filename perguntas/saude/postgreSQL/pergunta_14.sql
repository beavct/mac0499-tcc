SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    COUNT(DISTINCT saude.co_unidade) AS ambulatorios_especializados_publicos
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte2 dom2 
  ON s.cd_setor = dom2.cd_setor
LEFT JOIN culturaeduca.datasets.eq_saude_2025 saude 
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade AND a.at_04_conv_05 = '1'
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
  AND COALESCE(dom2.v00485, 0) = 0
GROUP BY s.nm_mun, s.nm_dist, s.cd_setor;
