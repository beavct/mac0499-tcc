SELECT DISTINCT
    sem.co_entidade AS id_escola,
    msem.no_entidade AS nome_escola
FROM culturaeduca.datasets.eq_educacao_basica_2024 sem
JOIN culturaeduca.datasets.microdados_ed_basica_2024 msem
  ON msem.co_entidade = sem.co_entidade AND msem.nu_ano_censo = sem.nu_ano_censo
WHERE msem.qt_tur_inf_cre = 0
  AND EXISTS (
      SELECT 1
      FROM culturaeduca.datasets.eq_educacao_basica_2024 com
      JOIN culturaeduca.datasets.microdados_ed_basica_2024 mcom
        ON mcom.co_entidade = com.co_entidade AND mcom.nu_ano_censo = com.nu_ano_censo
      WHERE mcom.qt_tur_inf_cre > 0
        AND com.co_entidade <> sem.co_entidade
        AND ST_DWithin(sem._geog, com._geog, 2000)
  )
ORDER BY nome_escola;
