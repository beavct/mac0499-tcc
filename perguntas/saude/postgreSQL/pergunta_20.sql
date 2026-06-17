SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    saude.co_unidade AS id_unidade,
    saude.no_fantasia AS nome_unidade,
    COALESCE(carac.v00006, 0) AS moradores_improvisados
FROM culturaeduca.datasets.eq_saude_2025 saude
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte1 carac 
  ON s.cd_setor = carac.cd_setor
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
  AND a.at_07_conv_06 = '1'
  AND COALESCE(carac.v00006, 0) > 0
ORDER BY moradores_improvisados DESC;
