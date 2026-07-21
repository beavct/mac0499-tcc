MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE s.situacao = 'Rural'
  AND saude.at_02_conv_01 = true
WITH DISTINCT m, s
RETURN m.nm_mun AS municipio,
       sum(s.v0001) AS populacao_rural_atendida
ORDER BY populacao_rural_atendida DESC;
