MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)

OPTIONAL MATCH (s)-[:TEM_PERFIL]->(r:PerfilRacaCor)
OPTIONAL MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)

WITH m.nm_mun AS municipio, d.nm_dist AS distrito,
     sum(coalesce(r.v01320, 0)) AS populacao_parda,
     sum(coalesce(e.qt_tur_bas_d, 0)) AS turmas_diurnas

RETURN municipio, distrito, populacao_parda, turmas_diurnas
ORDER BY populacao_parda DESC;
