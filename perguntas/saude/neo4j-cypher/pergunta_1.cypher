MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(c:PerfilDomiciliosParte1)
WITH m, sum(coalesce(c.v00002, 0)) AS domicilios_improvisados

OPTIONAL MATCH (m)<-[:PARTE_DE]-(d2:Distrito)<-[:PARTE_DE*1..3]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_01_conv_01 = true

RETURN m.nm_mun AS municipio, 
       domicilios_improvisados, 
       count(DISTINCT saude) AS hospitais_internacao_sus
ORDER BY domicilios_improvisados DESC;
