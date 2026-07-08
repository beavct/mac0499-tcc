WITH domicilios_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        SUM(COALESCE(carac.v00001, 0)) AS domicilios_permanentes_ocupados
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte1 carac
      ON s.cd_setor = carac.cd_setor
    GROUP BY s.nm_mun, s.nm_dist
),
internacao_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        COUNT(DISTINCT saude.co_unidade) AS hospitais_internacao_sus
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.eq_saude_2025 saude
      ON ST_Contains(s._geom, saude._geom)
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON saude.co_unidade = a.co_unidade AND a.at_01_conv_01 = '1'
    GROUP BY s.nm_mun, s.nm_dist
)
SELECT
    d.municipio,
    d.distrito,
    d.domicilios_permanentes_ocupados,
    i.hospitais_internacao_sus
FROM domicilios_por_distrito d
JOIN internacao_por_distrito i
  ON d.municipio = i.municipio AND d.distrito = i.distrito
WHERE i.hospitais_internacao_sus > 5
ORDER BY d.domicilios_permanentes_ocupados DESC;
