MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(c:PerfilDomiciliosParte1)
WITH m, d, sum(coalesce(c.v00001, 0)) AS domicilios_permanentes_ocupados

MATCH (d)<-[:PARTE_DE*1..3]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_01_conv_01 = true
WITH m, d, domicilios_permanentes_ocupados, count(DISTINCT saude) AS hospitais_internacao_sus
WHERE hospitais_internacao_sus > 5

RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       domicilios_permanentes_ocupados, 
       hospitais_internacao_sus
ORDER BY domicilios_permanentes_ocupados DESC;
