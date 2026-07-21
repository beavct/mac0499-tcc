MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(a:PerfilAlfabetizacao)
WITH m, sum(coalesce(a.v00644, 0) - COALESCE(a.v00748, 0)) AS total_jovens_15_19_analfabetos

OPTIONAL MATCH (m)<-[:PARTE_DE]-(d2:Distrito)<-[:PARTE_DE*1..3]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WITH m, total_jovens_15_19_analfabetos, sum(coalesce(e.qt_tur_eja_med, 0)) AS total_turmas_eja_medio

RETURN m.nm_mun AS municipio,
       total_jovens_15_19_analfabetos,
       total_turmas_eja_medio
ORDER BY total_jovens_15_19_analfabetos DESC;
