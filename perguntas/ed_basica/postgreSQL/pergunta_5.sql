SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    m.co_entidade AS id_escola,
    m.no_entidade AS nome_escola,
    m.qt_tur_inf_cre AS qtd_turmas_creche,
    m.qt_tur_med AS qtd_turmas_medio
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
  ON m.co_entidade = eq.co_entidade 
 AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, eq._geom)
WHERE m.qt_tur_inf_cre > 0
  AND m.qt_tur_med > 0
ORDER BY s.nm_mun, s.nm_dist, m.no_entidade;