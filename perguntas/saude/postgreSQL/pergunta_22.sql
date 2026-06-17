SELECT 
    s.nm_mun AS municipio,
    s.cd_subdist AS subdistrito,
    COUNT(DISTINCT saude.co_unidade) AS total_hospitais_internacao
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.eq_saude_2025 saude 
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
  AND a.at_01_conv_01 = '1'
GROUP BY s.nm_mun, s.cd_subdist
ORDER BY total_hospitais_internacao DESC;
