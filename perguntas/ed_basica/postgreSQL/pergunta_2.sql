SELECT 
    s.nm_mun AS municipio,
    CASE 
        WHEN m.tp_dependencia = '1' THEN 'Federal'
        WHEN m.tp_dependencia = '2' THEN 'Estadual'
        WHEN m.tp_dependencia = '3' THEN 'Municipal'
        WHEN m.tp_dependencia = '4' THEN 'Privada'
        ELSE 'Não Informado'
    END AS dependencia_adm,
    COUNT(DISTINCT m.co_entidade) AS qtd_escolas,
    ROUND(
        COUNT(DISTINCT m.co_entidade) * 100.0 / SUM(COUNT(DISTINCT m.co_entidade)) OVER(PARTITION BY s.nm_mun), 2
    ) AS percentual_no_municipio
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
  ON m.co_entidade = eq.co_entidade 
 AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, eq._geom)
GROUP BY s.nm_mun, m.tp_dependencia
ORDER BY s.nm_mun, m.tp_dependencia;