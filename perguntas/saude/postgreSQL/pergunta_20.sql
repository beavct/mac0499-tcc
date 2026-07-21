WITH ambulatorios_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        COUNT(DISTINCT saude.co_unidade) AS ambulatorios_sus
    FROM culturaeduca.datasets.eq_saude_2025 saude
    JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
      ON ST_Contains(s._geom, saude._geom)
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON saude.co_unidade = a.co_unidade AND a.at_02_conv_01 = '1' -- Ambulatorial - SUS
    GROUP BY s.nm_mun, s.nm_dist
)
SELECT
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    saude.co_unidade AS id_unidade_internacao,
    saude.no_fantasia AS nome_unidade_internacao,
    COALESCE(amb.ambulatorios_sus, 0) AS ambulatorios_sus_no_distrito
FROM culturaeduca.datasets.eq_saude_2025 saude
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade AND a.at_01_conv_01 = '1' -- Internação - SUS
LEFT JOIN ambulatorios_por_distrito amb
  ON s.nm_mun = amb.municipio AND s.nm_dist = amb.distrito
ORDER BY ambulatorios_sus_no_distrito DESC, municipio, distrito;
