MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
  AND (e.in_quadra_esportes_coberta = true OR e.in_quadra_esportes_descoberta = true)
RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       count(e) AS escolas_com_quadra
ORDER BY municipio, escolas_com_quadra DESC;