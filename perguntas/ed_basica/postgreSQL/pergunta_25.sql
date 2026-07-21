WITH escolas_em AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        m.co_entidade AS id_escola,
        m.no_entidade AS nome_escola
    FROM culturaeduca.datasets.microdados_ed_basica_2024 m
    JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
      ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
    JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
      ON ST_Contains(s._geom, eq._geom)
    WHERE m.qt_tur_med > 0
),
distritos_uma_em AS (
    SELECT municipio, distrito
    FROM escolas_em
    GROUP BY municipio, distrito
    HAVING COUNT(DISTINCT id_escola) = 1
)
SELECT
    e.municipio,
    e.distrito,
    e.id_escola,
    e.nome_escola
FROM escolas_em e
JOIN distritos_uma_em u
  ON e.municipio = u.municipio AND e.distrito = u.distrito
ORDER BY e.municipio, e.distrito;
