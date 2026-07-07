MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDemografia)
WITH m, d, sum(coalesce(p.v01012, 0) + coalesce(p.v01025, 0)) AS total_jovens_15_19

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WITH m, d, total_jovens_15_19, count(DISTINCT CASE WHEN e.qt_tur_esp_cc > 0 THEN e END) AS escolas_com_inclusiva

RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       total_jovens_15_19, 
       escolas_com_inclusiva
ORDER BY escolas_com_inclusiva ASC, total_jovens_15_19 DESC;