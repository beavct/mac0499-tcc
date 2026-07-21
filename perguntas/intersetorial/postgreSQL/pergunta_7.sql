SELECT DISTINCT
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    COALESCE(ent.v05013, 0) AS domicilios_sem_iluminacao
FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_entorno_domicilios ent
  ON s.cd_setor = ent.cd_setor
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
  ON ST_Contains(s._geom, eq._geom)
JOIN culturaeduca.datasets.microdados_ed_basica_2024 m
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
WHERE (m.qt_tur_eja_fund > 0 OR m.qt_tur_eja_med > 0)
  AND COALESCE(ent.v05013, 0) > 30
  AND NOT EXISTS (
      SELECT 1
      FROM culturaeduca.datasets.eq_saude_2025 saude
      JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
        ON saude.co_unidade = a.co_unidade AND a.at_04_conv_01 = '1'
      WHERE ST_Contains(s._geom, saude._geom)
  )
ORDER BY domicilios_sem_iluminacao DESC;
