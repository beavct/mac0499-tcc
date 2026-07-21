WITH entorno_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        SUM(COALESCE(e.v05007, 0)) AS dom_sem_pavimentacao,
        SUM(COALESCE(e.v05022, 0)) AS dom_sem_calcada
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_entorno_domicilios e
      ON s.cd_setor = e.cd_setor
    GROUP BY s.nm_mun, s.nm_dist
),
escolas_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        COUNT(DISTINCT m.co_entidade) AS escolas_fund_publicas
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq ON ST_Contains(s._geom, eq._geom)
    JOIN culturaeduca.datasets.microdados_ed_basica_2024 m
      ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
    WHERE m.tp_dependencia IN ('1', '2', '3') AND m.qt_tur_fund > 0
    GROUP BY s.nm_mun, s.nm_dist
),
urgencia_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        COUNT(DISTINCT saude.co_unidade) AS unidades_urgencia_sus
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.eq_saude_2025 saude ON ST_Contains(s._geom, saude._geom)
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON saude.co_unidade = a.co_unidade AND a.at_04_conv_01 = '1'
    GROUP BY s.nm_mun, s.nm_dist
)
SELECT
    en.municipio,
    en.distrito,
    en.dom_sem_pavimentacao,
    en.dom_sem_calcada,
    es.escolas_fund_publicas,
    COALESCE(u.unidades_urgencia_sus, 0) AS unidades_urgencia_sus
FROM entorno_por_distrito en
JOIN escolas_por_distrito es
  ON en.municipio = es.municipio AND en.distrito = es.distrito
LEFT JOIN urgencia_por_distrito u
  ON en.municipio = u.municipio AND en.distrito = u.distrito
WHERE en.dom_sem_pavimentacao > 1000
  AND en.dom_sem_calcada > 1000
  AND es.escolas_fund_publicas > 5
  AND COALESCE(u.unidades_urgencia_sus, 0) < 3
ORDER BY en.dom_sem_pavimentacao DESC;
