WITH populacao_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        SUM(COALESCE(b.v0001, 0)) AS populacao_total
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_basico b
      ON s.cd_setor = b.cd_setor
    GROUP BY s.nm_mun, s.nm_dist
),
fossa_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        SUM(COALESCE(dom2.v00488, 0)) AS domicilios_fossa_rudimentar
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte2 dom2
      ON s.cd_setor = dom2.cd_setor
    GROUP BY s.nm_mun, s.nm_dist
)
SELECT
    p.municipio,
    p.distrito,
    p.populacao_total,
    COALESCE(f.domicilios_fossa_rudimentar, 0) AS domicilios_fossa_rudimentar,
    ROUND((1000.0 * COALESCE(f.domicilios_fossa_rudimentar, 0) / NULLIF(p.populacao_total, 0))::numeric, 2) AS fossa_por_mil_habitantes
FROM populacao_por_distrito p
LEFT JOIN fossa_por_distrito f
  ON p.municipio = f.municipio AND p.distrito = f.distrito
ORDER BY fossa_por_mil_habitantes DESC NULLS LAST, domicilios_fossa_rudimentar DESC;
