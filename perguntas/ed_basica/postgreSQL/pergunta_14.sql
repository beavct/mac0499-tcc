WITH criancas_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        SUM(COALESCE(demo.v01031, 0)) AS populacao_infantil_distrito
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_demografia demo
      ON s.cd_setor = demo.cd_setor
    GROUP BY s.nm_mun, s.nm_dist
)
SELECT
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    m.co_entidade AS id_escola,
    m.no_entidade AS nome_escola,
    c.populacao_infantil_distrito
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
  ON ST_Contains(s._geom, eq._geom)
JOIN criancas_por_distrito c
  ON s.nm_mun = c.municipio AND s.nm_dist = c.distrito
WHERE m.tp_dependencia = '4'
  AND m.qt_tur_inf > 0
ORDER BY c.populacao_infantil_distrito DESC, m.co_entidade;
