WITH jovens_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        SUM(COALESCE(demo.v01034, 0)) AS total_jovens_15_19
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_demografia demo
      ON s.cd_setor = demo.cd_setor
    GROUP BY s.nm_mun, s.nm_dist
),
escolas_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        COUNT(DISTINCT CASE WHEN m.qt_tur_esp_cc > 0 THEN m.co_entidade END) AS escolas_com_inclusiva
    FROM culturaeduca.datasets.microdados_ed_basica_2024 m
    JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
      ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
    JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
      ON ST_Contains(s._geom, eq._geom)
    GROUP BY s.nm_mun, s.nm_dist
)
SELECT
    j.municipio,
    j.distrito,
    j.total_jovens_15_19,
    COALESCE(e.escolas_com_inclusiva, 0) AS escolas_com_inclusiva
FROM jovens_por_distrito j
LEFT JOIN escolas_por_distrito e
  ON j.municipio = e.municipio AND j.distrito = e.distrito
ORDER BY escolas_com_inclusiva ASC, total_jovens_15_19 DESC;