WITH responsaveis_por_bairro AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_bairro AS bairro,
        SUM(COALESCE(dom2.v00092, 0)) AS responsaveis_raca_amarela
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte2 dom2
      ON s.cd_setor = dom2.cd_setor
    WHERE s.nm_bairro IS NOT NULL AND s.nm_bairro <> '.'
    GROUP BY s.nm_mun, s.nm_bairro
),
urgencia_por_bairro AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_bairro AS bairro,
        COUNT(DISTINCT saude.co_unidade) AS urgencia_privada
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.eq_saude_2025 saude
      ON ST_Contains(s._geom, saude._geom)
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON saude.co_unidade = a.co_unidade AND a.at_04_conv_06 = '1'
    WHERE s.nm_bairro IS NOT NULL AND s.nm_bairro <> '.'
    GROUP BY s.nm_mun, s.nm_bairro
)
SELECT
    r.municipio,
    r.bairro,
    r.responsaveis_raca_amarela,
    COALESCE(u.urgencia_privada, 0) AS urgencia_privada
FROM responsaveis_por_bairro r
LEFT JOIN urgencia_por_bairro u
  ON r.municipio = u.municipio AND r.bairro = u.bairro
ORDER BY r.responsaveis_raca_amarela DESC;
