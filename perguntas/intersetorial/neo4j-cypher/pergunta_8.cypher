MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(c:PerfilDomiciliosParte1)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
WITH m, d, sum(coalesce(c.v00008, 0)) AS total_dom_criancas
WHERE total_dom_criancas > 5000

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.qt_tur_inf_cre > 0
WITH m, d, total_dom_criancas, count(DISTINCT e) AS creches

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(s3:SetorCensitario)<-[:LOCALIZADA_EM]-(es:EquipamentoSaude)
WHERE es.at_01_conv_01 = true

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       total_dom_criancas,
       creches,
       count(DISTINCT es) AS unidades_internacao_sus
ORDER BY total_dom_criancas DESC;