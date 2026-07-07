SELECT 
    s.nm_mun AS municipio,
    s.nm_bairro AS bairro,
    saude.co_unidade AS id_unidade,
    saude.no_fantasia AS nome_unidade,
    SUM(COALESCE(carac.v00085, 0)) AS moradores_casa_vila
FROM culturaeduca.datasets.eq_saude_2025 saude
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte1 carac 
  ON s.cd_setor = carac.cd_setor
WHERE a.at_06_conv_06 = '1'
  AND s.nm_bairro IS NOT NULL AND s.nm_bairro <> '.'
GROUP BY s.nm_mun, s.nm_bairro, saude.co_unidade, saude.no_fantasia
ORDER BY moradores_casa_vila DESC;
