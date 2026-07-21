SELECT
    esc.co_entidade AS id_escola,
    m.no_entidade AS nome_escola
FROM culturaeduca.datasets.eq_educacao_basica_2024 esc
JOIN culturaeduca.datasets.microdados_ed_basica_2024 m
  ON m.co_entidade = esc.co_entidade AND m.nu_ano_censo = esc.nu_ano_censo
WHERE NOT EXISTS (
    SELECT 1
    FROM culturaeduca.datasets.eq_saude_2025 saude
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON a.co_unidade = saude.co_unidade AND a.at_06_conv_01 = '1'
    WHERE ST_DWithin(esc._geog, saude._geog, 5000)
)
ORDER BY nome_escola;
