-- Agrega domicílios permanentes ocupados e escolas (total e com Educação
-- Especial Inclusiva) separadamente por distrito, evitando descartar escolas
-- em setores sem linha na tabela de domicílios.
WITH domicilios_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        SUM(COALESCE(ascdp.v00004, 0)) AS total_domicilios
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte1 ascdp
      ON s.cd_setor = ascdp.cd_setor
    GROUP BY s.nm_mun, s.nm_dist
),
escolas_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        COUNT(DISTINCT m.co_entidade) AS total_escolas,
        COUNT(DISTINCT CASE WHEN m.qt_tur_esp_cc > 0 THEN m.co_entidade END) AS escolas_com_inclusiva
    FROM culturaeduca.datasets.microdados_ed_basica_2024 m
    JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
      ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
    JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
      ON ST_Contains(s._geom, eq._geom)
    GROUP BY s.nm_mun, s.nm_dist
)
SELECT
    d.municipio,
    d.distrito,
    d.total_domicilios,
    COALESCE(e.total_escolas, 0) AS total_escolas,
    COALESCE(e.escolas_com_inclusiva, 0) AS escolas_com_inclusiva
FROM domicilios_por_distrito d
LEFT JOIN escolas_por_distrito e
  ON d.municipio = e.municipio AND d.distrito = e.distrito
ORDER BY total_domicilios DESC;
