SELECT
    esc.co_entidade AS id_escola,
    esc.no_entidade AS nome_escola,
    s.nm_mun AS municipio,
    COALESCE(dom2.v00401, 0) AS domicilios_lixo_irregular_no_setor
FROM culturaeduca.datasets.eq_educacao_basica_2024 esc
JOIN culturaeduca.datasets.microdados_ed_basica_2024 m
  ON m.co_entidade = esc.co_entidade AND m.nu_ano_censo = esc.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
  ON ST_Contains(s._geom, esc._geom)
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte2 dom2
  ON dom2.cd_setor = s.cd_setor
WHERE m.tp_dependencia IN ('1', '2', '3')
  AND COALESCE(dom2.v00401, 0) > 30
  AND NOT EXISTS (
      SELECT 1
      FROM culturaeduca.datasets.eq_saude_2025 vig
      JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
        ON a.co_unidade = vig.co_unidade AND a.at_06_conv_01 = '1'
      WHERE ST_DWithin(esc._geog, vig._geog, 4000)
  )
ORDER BY domicilios_lixo_irregular_no_setor DESC;
