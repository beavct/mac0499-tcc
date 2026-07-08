WITH escolas_com_lab_por_distrito AS (
    SELECT
        s.nm_mun AS municipio,
        s.nm_dist AS distrito,
        COUNT(DISTINCT m.co_entidade) AS escolas_com_laboratorio
    FROM culturaeduca.datasets.microdados_ed_basica_2024 m
    JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
      ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
    JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
      ON ST_Contains(s._geom, eq._geom)
    WHERE m.in_laboratorio_ciencias = '1'
    GROUP BY s.nm_mun, s.nm_dist
    HAVING COUNT(DISTINCT m.co_entidade) >= 5
)
SELECT
    s.nm_mun AS municipio,
    s.nm_dist AS distrito,
    lab.escolas_com_laboratorio,
    m.co_entidade AS id_escola_sem_lab,
    m.no_entidade AS nome_escola_sem_lab
FROM culturaeduca.datasets.microdados_ed_basica_2024 m
JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq
  ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s
  ON ST_Contains(s._geom, eq._geom)
JOIN escolas_com_lab_por_distrito lab
  ON s.nm_mun = lab.municipio AND s.nm_dist = lab.distrito
WHERE m.in_laboratorio_ciencias = '0'
ORDER BY lab.escolas_com_laboratorio DESC, municipio, distrito;
