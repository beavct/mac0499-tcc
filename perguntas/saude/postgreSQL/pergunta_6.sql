SELECT
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    (COALESCE(demo.v01040, 0) + COALESCE(demo.v01041, 0)) AS idosos_60_mais
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_demografia demo
  ON s.cd_setor = demo.cd_setor
WHERE (COALESCE(demo.v01040, 0) + COALESCE(demo.v01041, 0)) > 50
  AND NOT EXISTS (
      SELECT 1
      FROM culturaeduca.datasets.eq_saude_2025 saude
      JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
        ON saude.co_unidade = a.co_unidade AND a.at_04_conv_01 = '1'
      WHERE ST_Contains(s._geom, saude._geom)
  )
ORDER BY idosos_60_mais DESC;
