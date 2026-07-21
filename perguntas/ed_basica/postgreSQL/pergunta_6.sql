SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    COALESCE(alf.v00901, 0) AS nao_alfabetizados_15_anos_mais
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_alfabetizacao alf 
  ON s.cd_setor = alf.cd_setor
LEFT JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
  ON ST_Contains(s._geom, eq._geom)
WHERE eq.co_entidade IS NULL -- left join preenche com NULL
  AND COALESCE(alf.v00901, 0) > 0
ORDER BY nao_alfabetizados_15_anos_mais DESC, s.cd_setor
LIMIT 20;