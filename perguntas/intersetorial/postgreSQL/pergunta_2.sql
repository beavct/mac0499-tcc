SELECT
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    COALESCE(carac.v00006, 0) AS moradores_dom_improvisados
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte1 carac
  ON s.cd_setor = carac.cd_setor
WHERE COALESCE(carac.v00006, 0) > 50
  AND NOT EXISTS (
    SELECT 1 FROM culturaeduca.datasets.eq_educacao_basica_2024 eq
    WHERE ST_Contains(s._geom, eq._geom)
  )
  AND NOT EXISTS (
    SELECT 1 FROM culturaeduca.datasets.eq_saude_2025 saude
    WHERE ST_Contains(s._geom, saude._geom)
  )
ORDER BY moradores_dom_improvisados DESC;