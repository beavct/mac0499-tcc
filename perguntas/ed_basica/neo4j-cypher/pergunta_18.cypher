MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(a:PerfilAlfabetizacao)
MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
RETURN m.nm_mun AS municipio, 
       sum(coalesce(a.v00644, 0)) AS total_jovens_15_19_analfabetos, 
       sum(coalesce(e.qt_tur_eja_med, 0)) AS total_turmas_eja_medio
ORDER BY total_jovens_15_19_analfabetos DESC;