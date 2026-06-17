MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDemografia)
MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
  AND e.tp_dependencia = 4
  AND e.qt_tur_inf > 0
RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       e.id_aparelho AS id_escola, 
       e.nm_aparelho AS nome_escola, 
       sum(coalesce(p.v01020, 0) + coalesce(p.v01009, 0)) AS populacao_infantil_distrito
ORDER BY populacao_infantil_distrito DESC;