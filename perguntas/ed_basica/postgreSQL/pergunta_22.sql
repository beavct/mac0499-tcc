WITH populacao_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        SUM(COALESCE(raca.v01320, 0)) AS populacao_parda
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_raca_cor raca
      ON s.cd_setor = raca.cd_setor
    GROUP BY s.nm_mun, s.nm_dist
),
turmas_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        SUM(m.qt_tur_bas_d) AS turmas_diurnas
    FROM culturaeduca.datasets.microdados_ed_basica_2024 m
    JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
      ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
    JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
      ON ST_Contains(s._geom, eq._geom)
    GROUP BY s.nm_mun, s.nm_dist
)
SELECT
    p.municipio,
    p.distrito,
    p.populacao_parda,
    COALESCE(t.turmas_diurnas, 0) AS turmas_diurnas
FROM populacao_por_distrito p
LEFT JOIN turmas_por_distrito t
  ON p.municipio = t.municipio AND p.distrito = t.distrito
ORDER BY p.populacao_parda DESC;
