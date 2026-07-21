SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    dist_par.total_familias_estendidas,
    COUNT(DISTINCT m.co_entidade) AS escolas_infantil_integral
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
  ON m.co_entidade = eq.co_entidade 
 AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, eq._geom)
JOIN ( -- Famílias estendidas
    SELECT s2.nm_mun, s2.nm_dist, SUM(COALESCE(p.v01211, 0)) AS total_familias_estendidas
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s2
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_parentesco p 
      ON s2.cd_setor = p.cd_setor
    GROUP BY s2.nm_mun, s2.nm_dist
) dist_par 
  ON s.nm_mun = dist_par.nm_mun 
 AND s.nm_dist = dist_par.nm_dist
WHERE m.qt_tur_inf_int > 0
GROUP BY s.nm_mun, s.nm_dist, dist_par.total_familias_estendidas
ORDER BY dist_par.total_familias_estendidas DESC;