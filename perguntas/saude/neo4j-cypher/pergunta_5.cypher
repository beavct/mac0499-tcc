MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(c:PerfilDomiciliosParte3)
MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_06_conv_01 = true
  AND c.v00591 > 0
RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       s.cd_setor AS codigo_setor, 
       c.v00591 AS crianças_rudimentar, 
       count(DISTINCT saude) AS qtd_saude_sus
ORDER BY crianças_rudimentar DESC;
