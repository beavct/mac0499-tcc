MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(r:PerfilRacaCor)
WITH m, d, sum(coalesce(r.v01320, 0)) AS populacao_parda

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WITH m, d, populacao_parda, sum(coalesce(e.qt_tur_bas_d, 0)) AS turmas_diurnas

RETURN m.nm_mun AS municipio, d.nm_dist AS distrito, populacao_parda, turmas_diurnas
ORDER BY populacao_parda DESC;
