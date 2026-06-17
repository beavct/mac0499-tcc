SELECT
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    dist_quadra.escolas_com_quadra,
    COUNT(DISTINCT m.co_entidade) AS escolas_sem_quadra,
    m.co_entidade AS id_escola_sem_quadra,
    m.no_entidade AS nome_escola_sem_quadra
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
  ON ST_Contains(s._geom, eq._geom)
JOIN (
    SELECT s2.nm_mun, s2.nm_dist, COUNT(DISTINCT m2.co_entidade) AS escolas_com_quadra
    FROM culturaeduca.datasets.microdados_ed_basica_2024 m2
    JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq2
      ON m2.co_entidade = eq2.co_entidade AND m2.nu_ano_censo = eq2.nu_ano_censo
    JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s2
      ON ST_Contains(s2._geom, eq2._geom)
    WHERE s2.cd_mun IN ('3550308', '3509502', '3548708')
      AND (m2.in_quadra_esportes_coberta = '1' OR m2.in_quadra_esportes_descoberta = '1')
    GROUP BY s2.nm_mun, s2.nm_dist
    HAVING COUNT(DISTINCT m2.co_entidade) >= 5
) dist_quadra ON s.nm_mun = dist_quadra.nm_mun AND s.nm_dist = dist_quadra.nm_dist
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
  AND m.in_quadra_esportes_coberta = '0'
  AND m.in_quadra_esportes_descoberta = '0'
GROUP BY s.nm_mun, s.nm_dist, dist_quadra.escolas_com_quadra, m.co_entidade, m.no_entidade
ORDER BY escolas_sem_quadra DESC;