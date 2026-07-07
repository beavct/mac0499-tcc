SELECT 
    s.nm_mun AS municipio,
    SUM(COALESCE(b.v0001, 0)) AS populacao_urbana_atendida_integral
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_basico b ON s.cd_setor = b.cd_setor
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq ON ST_Contains(s._geom, eq._geom)
JOIN culturaeduca.datasets.microdados_ed_basica_2024 m ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
WHERE s.situacao = 'Urbano'
  AND m.qt_tur_fund_int > 0
GROUP BY s.nm_mun
ORDER BY populacao_urbana_atendida_integral DESC;
