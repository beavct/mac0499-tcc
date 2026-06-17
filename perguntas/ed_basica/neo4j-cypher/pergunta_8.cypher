MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilParentesco)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
WITH m, d, sum(coalesce(p.v01211, 0)) AS total_familias_estendidas

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.qt_tur_inf_int > 0
WITH m, d, total_familias_estendidas, count(DISTINCT e) AS escolas_infantil_integral
WHERE escolas_infantil_integral > 0

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       total_familias_estendidas,
       escolas_infantil_integral
ORDER BY total_familias_estendidas DESC;