SELECT 
    s.nm_mun AS municipio,
    s.nm_bairro AS bairro,
    SUM(COALESCE(dom2.v00093, 0)) AS responsaveis_raca_amarela,
    COUNT(DISTINCT saude.co_unidade) AS urgencia_privada
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte2 dom2 
  ON s.cd_setor = dom2.cd_setor
LEFT JOIN culturaeduca.datasets.eq_saude_2025 saude 
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade AND a.at_03_conv_06 = '1'
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
  AND s.nm_bairro IS NOT NULL AND s.nm_bairro <> '.'
GROUP BY s.nm_mun, s.nm_bairro
ORDER BY responsaveis_raca_amarela DESC;
