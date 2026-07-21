SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    MAX(COALESCE(dom2.v00316, 0)) AS domicilios_esgoto_inexistente,
    COUNT(DISTINCT saude.co_unidade) AS unidades_vigilancia_sus
FROM culturaeduca.datasets.eq_saude_2025 saude
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte2 dom2
  ON s.cd_setor = dom2.cd_setor
WHERE a.at_06_conv_01 = '1' AND dom2.v00316 > 0
GROUP BY s.nm_mun, s.nm_dist, s.cd_setor
ORDER BY domicilios_esgoto_inexistente DESC;
