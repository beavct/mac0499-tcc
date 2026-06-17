MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
  AND s.v0001 > 1000

OPTIONAL MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)
OPTIONAL MATCH (s)<-[:LOCALIZADA_EM]-(es:EquipamentoSaude)

WITH m, d, s,
     count(DISTINCT e) AS qtd_escolas,
     count(DISTINCT es) AS qtd_saude,
     (count(DISTINCT e) + count(DISTINCT es)) AS total_equipamentos

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       s.cd_setor AS codigo_setor,
       s.v0001 AS populacao,
       qtd_escolas,
       qtd_saude,
       total_equipamentos
ORDER BY total_equipamentos ASC, populacao DESC
LIMIT 30;