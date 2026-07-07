SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    COALESCE(b.v0001, 0) AS total_moradores
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_basico b 
  ON s.cd_setor = b.cd_setor
LEFT JOIN culturaeduca.datasets.eq_saude_2025 saude 
  ON ST_Contains(s._geom, saude._geom)
WHERE COALESCE(b.v0001, 0) > 1000
  AND saude.co_unidade IS NULL
ORDER BY total_moradores DESC;
