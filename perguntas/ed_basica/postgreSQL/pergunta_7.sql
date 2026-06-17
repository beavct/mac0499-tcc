SELECT 
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    s.cd_setor AS codigo_setor,
    m.co_entidade AS id_escola,
    m.no_entidade AS nome_escola,
    m.qt_tur_med AS turmas_ensino_medio,
    m.qt_tur_bas_d AS turmas_diurno,
    COALESCE(dom2.v00094, 0) AS responsaveis_indigenas_casa
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
  ON m.co_entidade = eq.co_entidade 
 AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s 
  ON ST_Contains(s._geom, eq._geom)
-- TABELA REAL CORRIGIDA:
JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_domicilios_parte2 dom2
  ON s.cd_setor = dom2.cd_setor
WHERE s.cd_mun IN ('3550308', '3509502', '3548708')
  AND m.tp_dependencia IN ('1', '2', '3') -- Escolas Públicas
  AND m.qt_tur_med > 0                    -- Possui Ensino Médio
  AND m.qt_tur_bas_d > 0                  -- Possui Turno Diurno
  AND COALESCE(dom2.v00094, 0) > 0       -- Presença de responsáveis indígenas
ORDER BY responsaveis_indigenas_casa DESC;