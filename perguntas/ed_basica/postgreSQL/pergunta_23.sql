SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    COUNT(DISTINCT m.co_entidade) AS escolas_sem_saneamento_entorno
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, eq._geom)
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte2 dom2 
  ON s.cd_setor = dom2.cd_setor
WHERE m.tp_dependencia IN ('1', '2', '3')
  AND COALESCE(dom2.v00495, 0) > 0
GROUP BY s.nm_mun, s.nm_dist, s.cd_setor;
