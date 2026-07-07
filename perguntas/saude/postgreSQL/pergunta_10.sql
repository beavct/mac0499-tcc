SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    dist_pop.total_habitantes,
    COUNT(DISTINCT saude.co_unidade) AS qtd_ambulatorios_sus
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
LEFT JOIN culturaeduca.datasets.eq_saude_2025 saude 
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade AND a.at_02_conv_01 = '1'
JOIN (
    SELECT s2.nm_mun, s2.nm_dist, SUM(COALESCE(b.v0001, 0)) AS total_habitantes
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s2
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_basico b ON s2.cd_setor = b.cd_setor
    GROUP BY s2.nm_mun, s2.nm_dist
) dist_pop ON s.nm_mun = dist_pop.nm_mun AND s.nm_dist = dist_pop.nm_dist
GROUP BY s.nm_mun, s.nm_dist, dist_pop.total_habitantes
HAVING dist_pop.total_habitantes > 50000 AND COUNT(DISTINCT saude.co_unidade) < 3
ORDER BY dist_pop.total_habitantes DESC;
