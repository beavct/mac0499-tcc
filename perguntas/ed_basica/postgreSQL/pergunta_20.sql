WITH Setores AS (
    SELECT 
        s.cd_setor,
        s.nm_mun,
        s.nm_dist,
        COALESCE(ascdp.v00004, 0) AS domicilios
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte1 ascdp
      ON s.cd_setor = ascdp.cd_setor
    WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
),
Escolas AS (
    SELECT 
        s2.cd_setor,
        COUNT(DISTINCT m.co_entidade) AS total_escolas,
        COUNT(DISTINCT CASE WHEN m.qt_tur_esp_cc > 0 THEN m.co_entidade END) AS escolas_com_inclusiva
    FROM culturaeduca.datasets.microdados_ed_basica_2024 m
    JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
      ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
    JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s2 
      ON ST_Contains(s2._geom, eq._geom)
    GROUP BY s2.cd_setor
)
SELECT 
    setores.nm_mun AS municipio,
    setores.nm_dist AS distrito,
    SUM(setores.domicilios) AS total_domicilios,
    SUM(COALESCE(escolas.total_escolas, 0)) AS total_escolas,
    SUM(COALESCE(escolas.escolas_com_inclusiva, 0)) AS escolas_com_inclusiva
FROM Setores setores
LEFT JOIN Escolas escolas 
  ON setores.cd_setor = escolas.cd_setor
GROUP BY setores.nm_mun, setores.nm_dist
ORDER BY total_domicilios DESC;