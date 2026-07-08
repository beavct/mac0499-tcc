WITH escolas_em AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        m.co_entidade AS id_escola_em,
        m.no_entidade AS nome_escola_em
    FROM culturaeduca.datasets.microdados_ed_basica_2024 m
    JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
      ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
    JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
      ON ST_Contains(s._geom, eq._geom)
    WHERE m.qt_tur_med > 0
),
escolas_ef_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        COUNT(DISTINCT m.co_entidade) AS escolas_fundamental
    FROM culturaeduca.datasets.microdados_ed_basica_2024 m
    JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
      ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
    JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
      ON ST_Contains(s._geom, eq._geom)
    WHERE m.qt_tur_fund > 0
    GROUP BY s.nm_mun, s.nm_dist
)
SELECT
    em.municipio,
    em.distrito,
    em.id_escola_em,
    em.nome_escola_em,
    COALESCE(ef.escolas_fundamental, 0) AS escolas_fundamental_no_distrito
FROM escolas_em em
LEFT JOIN escolas_ef_por_distrito ef
  ON em.municipio = ef.municipio AND em.distrito = ef.distrito
ORDER BY escolas_fundamental_no_distrito DESC, em.municipio, em.distrito;
