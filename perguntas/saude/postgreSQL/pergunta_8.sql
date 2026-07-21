WITH domicilios_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        SUM(COALESCE(par.v01188, 0)) AS domicilios_chefia_feminina_sem_conjuge
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_parentesco par
      ON s.cd_setor = par.cd_setor
    WHERE s.nm_mun = 'Campinas'
    GROUP BY s.nm_mun, s.nm_dist
),
gratuidade_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        COUNT(DISTINCT saude.co_unidade) AS estabelecimentos_gratuidade
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.eq_saude_2025 saude
      ON ST_Contains(s._geom, saude._geom)
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON saude.co_unidade = a.co_unidade AND a.at_01_conv_07 = '1'
    WHERE s.nm_mun = 'Campinas'
    GROUP BY s.nm_mun, s.nm_dist
)
SELECT
    d.municipio,
    d.distrito,
    d.domicilios_chefia_feminina_sem_conjuge,
    COALESCE(g.estabelecimentos_gratuidade, 0) AS estabelecimentos_gratuidade
FROM domicilios_por_distrito d
LEFT JOIN gratuidade_por_distrito g
  ON d.municipio = g.municipio AND d.distrito = g.distrito
ORDER BY d.domicilios_chefia_feminina_sem_conjuge DESC;
