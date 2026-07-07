MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
RETURN m.nm_mun AS municipio,
       count(e) AS total_escolas
ORDER BY municipio, total_escolas DESC;
