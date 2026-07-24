WITH bairros_com_creche AS (
    SELECT DISTINCT s.nm_mun, s.nm_bairro
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
      ON ST_Contains(s._geom, eq._geom)
    JOIN culturaeduca.datasets.microdados_ed_basica_2024 m
      ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
    WHERE m.qt_tur_inf_cre > 0
      AND s.nm_bairro IS NOT NULL AND s.nm_bairro <> '.'
),
bairros_com_saude AS (
    SELECT DISTINCT s.nm_mun, s.nm_bairro
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.eq_saude_2025 saude
      ON ST_Contains(s._geom, saude._geom)
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON saude.co_unidade = a.co_unidade AND a.at_02_conv_01 = '1'
    WHERE s.nm_bairro IS NOT NULL AND s.nm_bairro <> '.'
)
SELECT c.nm_mun AS municipio, c.nm_bairro AS bairro
FROM bairros_com_creche c
WHERE NOT EXISTS (
    SELECT 1 FROM bairros_com_saude sd
    WHERE sd.nm_mun = c.nm_mun AND sd.nm_bairro = c.nm_bairro
)
ORDER BY municipio, bairro;
