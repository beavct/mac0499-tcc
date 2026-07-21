WITH criancas_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        SUM(COALESCE(carac.v00009, 0)) AS total_dom_criancas
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte1 carac
      ON s.cd_setor = carac.cd_setor
    GROUP BY s.nm_mun, s.nm_dist
),
creches_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        COUNT(DISTINCT m.co_entidade) AS creches
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq ON ST_Contains(s._geom, eq._geom)
    JOIN culturaeduca.datasets.microdados_ed_basica_2024 m
      ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
    WHERE m.qt_tur_inf_cre > 0
    GROUP BY s.nm_mun, s.nm_dist
),
internacao_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        COUNT(DISTINCT saude.co_unidade) AS unidades_internacao_sus
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.eq_saude_2025 saude ON ST_Contains(s._geom, saude._geom)
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON saude.co_unidade = a.co_unidade AND a.at_01_conv_01 = '1'
    GROUP BY s.nm_mun, s.nm_dist
)
SELECT
    c.municipio,
    c.distrito,
    c.total_dom_criancas,
    COALESCE(cr.creches, 0) AS creches,
    COALESCE(i.unidades_internacao_sus, 0) AS unidades_internacao_sus
FROM criancas_por_distrito c
LEFT JOIN creches_por_distrito cr
  ON c.municipio = cr.municipio AND c.distrito = cr.distrito
LEFT JOIN internacao_por_distrito i
  ON c.municipio = i.municipio AND c.distrito = i.distrito
WHERE c.total_dom_criancas > 0
ORDER BY c.total_dom_criancas DESC;
