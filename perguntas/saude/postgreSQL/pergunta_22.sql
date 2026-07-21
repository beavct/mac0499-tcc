WITH leitos_por_setor AS (
    SELECT
        s.nm_mun AS municipio,
        s.cd_subdist AS subdistrito,
        s.cd_setor AS codigo_setor,
        COUNT(DISTINCT a.co_unidade) AS leitos_no_setor
    FROM culturaeduca.datasets.dtb_setores_censitarios_2022 s
    LEFT JOIN culturaeduca.datasets.eq_saude_2025 saude
      ON ST_Contains(s._geom, saude._geom)
    LEFT JOIN culturaeduca.datasets.microdados_saude_2025_atendimentos a
      ON saude.co_unidade = a.co_unidade AND a.at_01_conv_01 = '1'
    GROUP BY s.nm_mun, s.cd_subdist, s.cd_setor
)
SELECT
    municipio,
    subdistrito,
    MAX(leitos_no_setor) - MIN(leitos_no_setor) AS disparidade_leitos,
    MAX(leitos_no_setor) AS max_leitos_setor,
    MIN(leitos_no_setor) AS min_leitos_setor
FROM leitos_por_setor
GROUP BY municipio, subdistrito
HAVING MAX(leitos_no_setor) - MIN(leitos_no_setor) > 0
ORDER BY disparidade_leitos DESC;
