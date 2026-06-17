SELECT
    s.nm_mun AS municipio,
    s.nm_bairro AS bairro,
    SUM(COALESCE(par.v01215, 0)) AS domicilios_unipessoais_femininos,
    COUNT(DISTINCT a.co_unidade) AS estabelecimentos_gratuidade
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_parentesco par
  ON s.cd_setor = par.cd_setor
LEFT JOIN culturaeduca.datasets.eq_saude_2025 saude
  ON ST_Contains(s._geom, saude._geom)
LEFT JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade AND a.at_01_conv_07 = '1'
WHERE s.nm_mun = 'Campinas'
  AND s.nm_bairro IS NOT NULL AND s.nm_bairro <> '.'
GROUP BY s.nm_mun, s.nm_bairro
ORDER BY domicilios_unipessoais_femininos DESC;
