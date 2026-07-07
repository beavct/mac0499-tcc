-- Agrega população analfabeta e turmas de EJA Médio separadamente por município
-- (evita o produto cartesiano entre setores e escolas do mesmo setor).
WITH analfabetos_por_mun AS (
    SELECT s.nm_mun AS municipio,
           SUM(COALESCE(alf.v00644, 0)) AS total_jovens_15_19_analfabetos
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_alfabetizacao alf
      ON s.cd_setor = alf.cd_setor
    GROUP BY s.nm_mun
),
eja_por_mun AS (
    SELECT s.nm_mun AS municipio,
           SUM(m.qt_tur_eja_med) AS total_turmas_eja_medio
    FROM culturaeduca.datasets.microdados_ed_basica_2024 m
    JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
      ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
    JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
      ON ST_Contains(s._geom, eq._geom)
    GROUP BY s.nm_mun
)
SELECT a.municipio,
       a.total_jovens_15_19_analfabetos,
       COALESCE(e.total_turmas_eja_medio, 0) AS total_turmas_eja_medio
FROM analfabetos_por_mun a
LEFT JOIN eja_por_mun e ON a.municipio = e.municipio
ORDER BY a.total_jovens_15_19_analfabetos DESC;
