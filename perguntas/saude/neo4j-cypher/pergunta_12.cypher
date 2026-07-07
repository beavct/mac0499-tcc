MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(r:PerfilRacaCor)
MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_07_conv_01 = true

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       sum(coalesce(r.v01318, 0)) AS populacao_negra,
       count(DISTINCT saude) AS centros_diagnose_sus
ORDER BY populacao_negra DESC;
