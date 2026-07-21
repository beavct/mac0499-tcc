MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(r:PerfilRacaCor)
WITH m, d, sum(coalesce(r.v01318, 0)) AS populacao_negra

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_03_conv_01 = true

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       populacao_negra,
       count(DISTINCT saude) AS centros_diagnose_sus
ORDER BY populacao_negra DESC;
