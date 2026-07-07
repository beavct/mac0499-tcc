MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(c:PerfilDomiciliosParte1)
WITH m, d, sum(coalesce(c.v00008, 0)) AS total_domicilios_com_criancas
WHERE total_domicilios_com_criancas > 5000

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.qt_tur_inf_cre > 0
WITH m, d, total_domicilios_com_criancas, count(DISTINCT e) AS qtd_escolas_creche
WHERE qtd_escolas_creche < 5

RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       total_domicilios_com_criancas, 
       qtd_escolas_creche
ORDER BY total_domicilios_com_criancas DESC;
