SELECT
    s.nm_mun AS municipio,
    s.nm_bairro AS bairro
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
  ON ST_Contains(s._geom, eq._geom)
JOIN culturaeduca.datasets.microdados_ed_basica_2024 m
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
  AND m.qt_tur_inf_cre > 0
  AND s.nm_bairro IS NOT NULL AND s.nm_bairro <> '.'
GROUP BY s.nm_mun, s.nm_bairro
HAVING NOT EXISTS (
    SELECT 1 FROM culturaeduca.datasets.eq_saude_2025 saude
    JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s2
      ON ST_Contains(s2._geom, saude._geom)
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
  ON saude.co_unidade = a.co_unidade
    WHERE s2.nm_bairro = s.nm_bairro AND s2.nm_mun = s.nm_mun
      AND a.at_02_conv_01 = '1'
)
ORDER BY municipio, bairro;