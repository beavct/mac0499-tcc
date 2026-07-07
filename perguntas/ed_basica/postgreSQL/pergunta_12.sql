SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    dist_crianca.total_domicilios_com_criancas,
    COUNT(DISTINCT CASE WHEN m.qt_tur_inf_cre > 0 THEN m.co_entidade END) AS qtd_escolas_creche
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
LEFT JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq ON ST_Contains(s._geom, eq._geom)
LEFT JOIN culturaeduca.datasets.microdados_ed_basica_2024 m ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
JOIN (
    SELECT s2.nm_mun, s2.nm_dist, SUM(COALESCE(ascdp.v00008, 0)) AS total_domicilios_com_criancas
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s2
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte1 ascdp ON s2.cd_setor = ascdp.cd_setor
    GROUP BY s2.nm_mun, s2.nm_dist
) dist_crianca ON s.nm_mun = dist_crianca.nm_mun AND s.nm_dist = dist_crianca.nm_dist
GROUP BY s.nm_mun, s.nm_dist, dist_crianca.total_domicilios_com_criancas
HAVING dist_crianca.total_domicilios_com_criancas > 5000 
   AND COUNT(DISTINCT CASE WHEN m.qt_tur_inf_cre > 0 THEN m.co_entidade END) < 5
ORDER BY total_domicilios_com_criancas DESC;
