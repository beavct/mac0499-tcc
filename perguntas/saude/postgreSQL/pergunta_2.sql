SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    saude.co_unidade AS id_unidade,
    saude.no_fantasia AS nome_unidade,
    (COALESCE(alf.v00644, 0) - (COALESCE(alf.v00657, 0) + COALESCE(alf.v00658, 0) + COALESCE(alf.v00659, 0) + COALESCE(alf.v00660, 0) + COALESCE(alf.v00661, 0))) AS jovens_15_19_analfabetos
FROM culturaeduca.datasets.eq_saude_2025 saude
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_alfabetizacao alf 
  ON s.cd_setor = alf.cd_setor
WHERE a.at_02_conv_01 = '1'
  AND (COALESCE(alf.v00644, 0) - (COALESCE(alf.v00657, 0) + COALESCE(alf.v00658, 0) + COALESCE(alf.v00659, 0) + COALESCE(alf.v00660, 0) + COALESCE(alf.v00661, 0))) > 0
ORDER BY jovens_15_19_analfabetos DESC;
