SELECT
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    dist_crianca.total_dom_criancas,
    COUNT(DISTINCT CASE WHEN m.qt_tur_inf_cre > 0 THEN m.co_entidade END) AS creches,
    COUNT(DISTINCT CASE WHEN a.at_01_conv_01 = '1' THEN saude.co_unidade END) AS unidades_internacao_sus
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
LEFT JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq ON ST_Contains(s._geom, eq._geom)
LEFT JOIN culturaeduca.datasets.microdados_ed_basica_2024 m ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
LEFT JOIN culturaeduca.datasets.eq_saude_2025 saude ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade
JOIN (
    SELECT s2.nm_mun, s2.nm_dist, SUM(COALESCE(carac.v00008, 0)) AS total_dom_criancas
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s2
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte1 carac ON s2.cd_setor = carac.cd_setor
    GROUP BY s2.nm_mun, s2.nm_dist
) dist_crianca ON s.nm_mun = dist_crianca.nm_mun AND s.nm_dist = dist_crianca.nm_dist
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
  AND dist_crianca.total_dom_criancas > 5000
GROUP BY s.nm_mun, s.nm_dist, dist_crianca.total_dom_criancas
ORDER BY total_dom_criancas DESC;