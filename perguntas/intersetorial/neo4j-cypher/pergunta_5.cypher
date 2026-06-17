MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']

OPTIONAL MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)
OPTIONAL MATCH (s)<-[:LOCALIZADA_EM]-(es:EquipamentoSaude)
WHERE es.at_02_conv_01 = true

WITH m, d, count(DISTINCT e) AS total_escolas, count(DISTINCT es) AS total_saude_sus
WHERE total_escolas > 0

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       total_escolas,
       total_saude_sus,
       round(toFloat(total_escolas) / CASE WHEN total_saude_sus = 0 THEN 1 ELSE total_saude_sus END, 2) AS razao_escola_saude
ORDER BY razao_escola_saude DESC;