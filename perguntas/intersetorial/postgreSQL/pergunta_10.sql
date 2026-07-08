WITH indigenas_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        SUM(COALESCE(dom2.v00094, 0)) AS responsaveis_indigenas
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte2 dom2
      ON s.cd_setor = dom2.cd_setor
    GROUP BY s.nm_mun, s.nm_dist
),
escolas_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        COUNT(DISTINCT m.co_entidade) AS escolas_fund_publicas
    FROM culturaeduca.datasets.eq_educacao_basica_2024 eq
    JOIN culturaeduca.datasets.microdados_ed_basica_2024 m
      ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
    JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
      ON ST_Contains(s._geom, eq._geom)
    WHERE m.tp_dependencia IN ('1', '2', '3')
      AND (m.qt_tur_fund_ai > 0 OR m.qt_tur_fund_af > 0)
    GROUP BY s.nm_mun, s.nm_dist
),
saude_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        COUNT(DISTINCT saude.co_unidade) AS unidades_ambulatoriais_sus
    FROM culturaeduca.datasets.eq_saude_2025 saude
    JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON saude.co_unidade = a.co_unidade AND a.at_02_conv_01 = '1'
    JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
      ON ST_Contains(s._geom, saude._geom)
    GROUP BY s.nm_mun, s.nm_dist
)
SELECT
    i.municipio,
    i.distrito,
    i.responsaveis_indigenas,
    COALESCE(e.escolas_fund_publicas, 0) AS escolas_fund_publicas,
    COALESCE(sd.unidades_ambulatoriais_sus, 0) AS unidades_ambulatoriais_sus
FROM indigenas_por_distrito i
LEFT JOIN escolas_por_distrito e
  ON i.municipio = e.municipio AND i.distrito = e.distrito
LEFT JOIN saude_por_distrito sd
  ON i.municipio = sd.municipio AND i.distrito = sd.distrito
ORDER BY i.responsaveis_indigenas DESC;
