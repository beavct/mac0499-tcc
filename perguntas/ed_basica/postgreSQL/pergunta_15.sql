WITH Setores AS (
    SELECT 
        s.cd_setor,
        s.nm_mun,
        s.nm_dist,
        COALESCE(s.nm_bairro, 'Não demarcado') AS nm_bairro,
        COALESCE(par.v01215, 0) AS chefia_feminina
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    JOIN culturaeduca.datasets.agregado_setores_censitarios_2022_parentesco par 
      ON s.cd_setor = par.cd_setor
),
Escolas AS (
    SELECT 
        s2.cd_setor,
        SUM(m.qt_tur_inf_cre_int) AS turmas_creche
    FROM culturaeduca.datasets.microdados_ed_basica_2024 m
    JOIN culturaeduca.datasets.eq_educacao_basica_2024 eq 
      ON m.co_entidade = eq.co_entidade AND m.nu_ano_censo = eq.nu_ano_censo
    JOIN culturaeduca.datasets.dtb_setores_censitarios_2022 s2 
      ON ST_Contains(s2._geom, eq._geom)
    GROUP BY s2.cd_setor
)
SELECT 
    setores.nm_mun AS municipio,
    setores.nm_dist AS distrito,
    setores.nm_bairro AS bairro,
    SUM(setores.chefia_feminina) AS chefia_feminina_unipessoal,
    SUM(COALESCE(escolas.turmas_creche, 0)) AS turmas_creche_integral
FROM Setores setores
LEFT JOIN Escolas escolas 
  ON setores.cd_setor = escolas.cd_setor
GROUP BY setores.nm_mun, setores.nm_dist, setores.nm_bairro
ORDER BY chefia_feminina_unipessoal DESC;