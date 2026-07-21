WITH escolas_por_municipio AS (
    SELECT
        s.nm_mun AS municipio,
        COUNT(DISTINCT m.co_entidade) AS escolas_publicas
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq ON ST_Contains(s._geom, eq._geom)
    JOIN culturaeduca.datasets.microdados_ed_basica_2024 m
      ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
    WHERE m.tp_dependencia IN ('1', '2', '3')
    GROUP BY s.nm_mun
),
saude_por_municipio AS (
    SELECT
        s.nm_mun AS municipio,
        COUNT(DISTINCT saude.co_unidade) AS unidades_ambulatorial_sus
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.eq_saude_2025 saude ON ST_Contains(s._geom, saude._geom)
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON saude.co_unidade = a.co_unidade AND a.at_02_conv_01 = '1'
    GROUP BY s.nm_mun
),
idosos_por_municipio AS (
    SELECT
        s.nm_mun AS municipio,
        SUM(COALESCE(demo.v01040, 0) + COALESCE(demo.v01041, 0)) AS populacao_60_mais
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_demografia demo
      ON s.cd_setor = demo.cd_setor
    GROUP BY s.nm_mun
)
SELECT
    e.municipio,
    e.escolas_publicas,
    COALESCE(sa.unidades_ambulatorial_sus, 0) AS unidades_ambulatorial_sus,
    i.populacao_60_mais,
    ROUND(e.escolas_publicas::numeric / NULLIF(sa.unidades_ambulatorial_sus, 0), 2) AS razao_escola_saude
FROM escolas_por_municipio e
JOIN idosos_por_municipio i ON e.municipio = i.municipio
LEFT JOIN saude_por_municipio sa ON e.municipio = sa.municipio
WHERE e.escolas_publicas > 0
ORDER BY razao_escola_saude DESC NULLS LAST;
