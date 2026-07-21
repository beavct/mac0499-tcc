MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(demo:PerfilDemografia)
WITH m, d, sum(coalesce(demo.v01031, 0)) AS criancas_0_4

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.qt_tur_inf_cre > 0
WITH m, d, criancas_0_4, sum(coalesce(e.qt_tur_inf_cre, 0)) AS turmas_creche

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       criancas_0_4,
       turmas_creche,
       CASE WHEN criancas_0_4 = 0 THEN null
            ELSE round(100.0 * turmas_creche / criancas_0_4, 2) END AS turmas_por_100_criancas
ORDER BY turmas_por_100_criancas ASC, criancas_0_4 DESC;