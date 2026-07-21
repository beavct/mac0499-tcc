MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.in_quadra_esportes = true
RETURN m.nm_mun AS municipio,
       count(e) AS escolas_com_quadra
ORDER BY municipio, escolas_com_quadra DESC;