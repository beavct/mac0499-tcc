WITH setores_rurais_atendidos AS (
    SELECT DISTINCT s.cd_setor, s.nm_mun
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.eq_saude_2025 saude
      ON ST_Contains(s._geom, saude._geom)
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON saude.co_unidade = a.co_unidade AND a.at_02_conv_01 = '1'
    WHERE s.situacao = 'Rural'
)
SELECT
    sra.nm_mun AS municipio,
    SUM(COALESCE(b.v0001, 0)) AS populacao_rural_atendida
FROM setores_rurais_atendidos sra
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_basico b
  ON sra.cd_setor = b.cd_setor
GROUP BY sra.nm_mun
ORDER BY populacao_rural_atendida DESC;
