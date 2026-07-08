WITH analfabetos_por_municipio AS (
    SELECT
        s.nm_mun AS municipio,
        SUM(COALESCE(alf.v00901, 0)) AS analfabetos_15_mais
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_alfabetizacao alf
      ON s.cd_setor = alf.cd_setor
    GROUP BY s.nm_mun
),
vigilancia_por_municipio AS (
    SELECT
        s.nm_mun AS municipio,
        COUNT(DISTINCT saude.co_unidade) AS unidades_vigilancia_publica
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.eq_saude_2025 saude
      ON ST_Contains(s._geom, saude._geom)
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON saude.co_unidade = a.co_unidade AND a.at_06_conv_05 = '1'
    GROUP BY s.nm_mun
)
SELECT
    m.municipio,
    m.analfabetos_15_mais,
    COALESCE(v.unidades_vigilancia_publica, 0) AS unidades_vigilancia_publica
FROM analfabetos_por_municipio m
LEFT JOIN vigilancia_por_municipio v
  ON m.municipio = v.municipio
ORDER BY m.analfabetos_15_mais DESC;
