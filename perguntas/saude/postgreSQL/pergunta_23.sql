WITH populacao_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        SUM(COALESCE(raca.v01389, 0)) AS populacao_amarela
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_raca_cor raca
      ON s.cd_setor = raca.cd_setor
    GROUP BY s.nm_mun, s.nm_dist
),
leitos_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        COUNT(DISTINCT saude.co_unidade) AS leitos_gratuitos
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.eq_saude_2025 saude
      ON ST_Contains(s._geom, saude._geom)
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON saude.co_unidade = a.co_unidade AND a.at_01_conv_07 = '1'
    GROUP BY s.nm_mun, s.nm_dist
)
SELECT
    p.municipio,
    p.distrito,
    p.populacao_amarela,
    COALESCE(l.leitos_gratuitos, 0) AS leitos_gratuitos
FROM populacao_por_distrito p
LEFT JOIN leitos_por_distrito l
  ON p.municipio = l.municipio AND p.distrito = l.distrito
ORDER BY p.populacao_amarela DESC;
