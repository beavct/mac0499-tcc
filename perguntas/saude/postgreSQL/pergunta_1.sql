WITH domicilios_por_municipio AS (
    SELECT
        s.nm_mun AS municipio,
        SUM(COALESCE(carac.v00002, 0)) AS domicilios_improvisados
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte1 carac
      ON s.cd_setor = carac.cd_setor
    GROUP BY s.nm_mun
),
internacao_por_municipio AS (
    SELECT
        s.nm_mun AS municipio,
        COUNT(DISTINCT saude.co_unidade) AS hospitais_internacao_sus
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.eq_saude_2025 saude
      ON ST_Contains(s._geom, saude._geom)
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON saude.co_unidade = a.co_unidade AND a.at_01_conv_01 = '1'
    GROUP BY s.nm_mun
)
SELECT
    d.municipio,
    d.domicilios_improvisados,
    COALESCE(i.hospitais_internacao_sus, 0) AS hospitais_internacao_sus
FROM domicilios_por_municipio d
LEFT JOIN internacao_por_municipio i
  ON d.municipio = i.municipio
ORDER BY d.domicilios_improvisados DESC;
