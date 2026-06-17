MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       count(e) AS total_escolas
ORDER BY municipio, total_escolas DESC;