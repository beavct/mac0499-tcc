SELECT
    esc.co_entidade AS id_escola,
    esc.no_entidade AS nome_escola,
    s.nm_mun AS municipio,
    COALESCE(demo.v01031, 0) AS criancas_0_4_no_setor
FROM culturaeduca.datasets.eq_educacao_basica_2024 esc
JOIN culturaeduca.datasets.microdados_ed_basica_2024 m
  ON m.co_entidade = esc.co_entidade AND m.nu_ano_censo = esc.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
  ON ST_Contains(s._geom, esc._geom)
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_demografia demo
  ON demo.cd_setor = s.cd_setor
WHERE m.qt_tur_inf > 0
  AND COALESCE(demo.v01031, 0) > 100
  AND NOT EXISTS (
      SELECT 1
      FROM culturaeduca.datasets.eq_educacao_basica_2024 outra
      JOIN culturaeduca.datasets.microdados_ed_basica_2024 mo
        ON mo.co_entidade = outra.co_entidade AND mo.nu_ano_censo = outra.nu_ano_censo
      WHERE mo.qt_tur_inf > 0
        AND outra.co_entidade <> esc.co_entidade
        AND ST_DWithin(esc._geog, outra._geog, 3000)
  )
ORDER BY criancas_0_4_no_setor DESC;
