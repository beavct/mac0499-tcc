SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    MAX(COALESCE(ascdp.v00085, 0)) AS moradores_casa_vila_condominio,
    COUNT(DISTINCT m.co_entidade) AS qtd_escolas_medio
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, eq._geom)
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte1 ascdp
  ON s.cd_setor = ascdp.cd_setor
WHERE m.qt_tur_med > 0
GROUP BY s.nm_mun, s.nm_dist, s.cd_setor
ORDER BY moradores_casa_vila_condominio DESC;
