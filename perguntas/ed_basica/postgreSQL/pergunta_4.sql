SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    COUNT(DISTINCT m.co_entidade) AS escolas_com_quadra
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
  ON m.co_entidade = eq.co_entidade 
 AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, eq._geom)
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
  AND (m.in_quadra_esportes_coberta = '1' OR m.in_quadra_esportes_descoberta = '1')
GROUP BY s.nm_mun, s.nm_dist
ORDER BY s.nm_mun, escolas_com_quadra DESC;