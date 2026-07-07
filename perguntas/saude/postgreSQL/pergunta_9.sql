SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    saude.co_unidade AS id_unidade,
    saude.no_fantasia AS nome_unidade,
    (COALESCE(demo.v01019, 0) + COALESCE(demo.v01032, 0)) AS populacao_idosa_70_mais
FROM culturaeduca.datasets.eq_saude_2025 saude
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_demografia demo 
  ON s.cd_setor = demo.cd_setor
WHERE a.at_06_conv_01 = '1'
  AND (COALESCE(demo.v01019, 0) + COALESCE(demo.v01032, 0)) > 0
ORDER BY populacao_idosa_70_mais DESC;
