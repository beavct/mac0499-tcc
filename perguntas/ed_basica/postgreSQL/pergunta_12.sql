WITH criancas_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        SUM(COALESCE(demo.v01009, 0) + COALESCE(demo.v01020, 0)) AS criancas_0_4
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_demografia demo
      ON s.cd_setor = demo.cd_setor
    GROUP BY s.nm_mun, s.nm_dist
),
turmas_creche_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        SUM(m.qt_tur_inf_cre) AS turmas_creche
    FROM culturaeduca.datasets.microdados_ed_basica_2024 m
    JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
      ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
    JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
      ON ST_Contains(s._geom, eq._geom)
    GROUP BY s.nm_mun, s.nm_dist
)
SELECT
    c.municipio,
    c.distrito,
    c.criancas_0_4,
    COALESCE(t.turmas_creche, 0) AS turmas_creche,
    ROUND((100.0 * COALESCE(t.turmas_creche, 0) / NULLIF(c.criancas_0_4, 0))::numeric, 2) AS turmas_por_100_criancas
FROM criancas_por_distrito c
LEFT JOIN turmas_creche_por_distrito t
  ON c.municipio = t.municipio AND c.distrito = t.distrito
ORDER BY turmas_por_100_criancas ASC NULLS LAST, c.criancas_0_4 DESC;
