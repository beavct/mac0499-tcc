SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    COALESCE(carac.v00087, 0) AS moradores_cortico,
    COUNT(DISTINCT saude.co_unidade) AS qtd_saude_sus
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte1 carac 
  ON s.cd_setor = carac.cd_setor
JOIN culturaeduca.datasets.eq_saude_2025 saude 
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
  AND a.at_05_conv_01 = '1'
  AND COALESCE(carac.v00087, 0) > 0
GROUP BY s.nm_mun, s.nm_dist, s.cd_setor, carac.v00087
ORDER BY moradores_cortico DESC;
