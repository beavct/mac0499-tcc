MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(c:PerfilDomiciliosParte1)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
WITH m, d, sum(coalesce(c.v00004, 0)) AS total_domicilios

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WITH m, d, total_domicilios, 
     count(DISTINCT e) AS total_escolas, 
     count(DISTINCT CASE WHEN e.qt_tur_esp_cc > 0 THEN e END) AS escolas_com_inclusiva

RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       total_domicilios, 
       total_escolas, 
       escolas_com_inclusiva
ORDER BY total_domicilios DESC;