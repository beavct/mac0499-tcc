SELECT
    urg.co_unidade AS id_urgencia,
    urg.no_fantasia AS nome_urgencia,
    s.nm_mun AS municipio,
    COALESCE(par.v01068, 0) AS responsaveis_60_mais_no_setor
FROM culturaeduca.datasets.eq_saude_2025 urg
JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos aurg
  ON aurg.co_unidade = urg.co_unidade AND aurg.at_04_conv_01 = '1'
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
  ON ST_Contains(s._geom, urg._geom)
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_parentesco par
  ON par.cd_setor = s.cd_setor
WHERE COALESCE(par.v01068, 0) > 80
  AND NOT EXISTS (
      SELECT 1
      FROM culturaeduca.datasets.eq_saude_2025 outra
      JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos ao
        ON ao.co_unidade = outra.co_unidade AND ao.at_04_conv_01 = '1'
      WHERE outra.co_unidade <> urg.co_unidade
        AND ST_DWithin(urg._geog, outra._geog, 10000)
  )
ORDER BY responsaveis_60_mais_no_setor DESC;
