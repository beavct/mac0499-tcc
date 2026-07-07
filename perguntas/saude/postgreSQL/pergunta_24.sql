SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    SUM(COALESCE(dom2.v00488, 0)) AS domicilios_fossa_rudimentar,
    COUNT(DISTINCT saude.co_unidade) AS unidades_urgencia_outros
FROM culturaeduca.datasets.eq_saude_2025 saude
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte2 dom2
  ON s.cd_setor = dom2.cd_setor
WHERE a.at_03_conv_07 = '1'
GROUP BY s.nm_mun, s.nm_dist, s.cd_setor
ORDER BY domicilios_fossa_rudimentar DESC;
