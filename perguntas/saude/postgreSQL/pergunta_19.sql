WITH populacao AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        SUM(COALESCE(b.v0001, 0)) AS populacao_total
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_basico b
      ON s.cd_setor = b.cd_setor
    WHERE s.nm_dist = 'Vila Sônia'
    GROUP BY s.nm_mun, s.nm_dist
),
urgencias AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        COUNT(DISTINCT saude.co_unidade) AS unidades_urgencia_sus
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.eq_saude_2025 saude
      ON ST_Contains(s._geom, saude._geom)
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON saude.co_unidade = a.co_unidade AND a.at_04_conv_01 = '1'
    WHERE s.nm_dist = 'Vila Sônia'
    GROUP BY s.nm_mun, s.nm_dist
)
SELECT
    p.municipio,
    p.distrito,
    p.populacao_total,
    COALESCE(u.unidades_urgencia_sus, 0) AS unidades_urgencia_sus
FROM populacao p
LEFT JOIN urgencias u
  ON p.municipio = u.municipio AND p.distrito = u.distrito;
