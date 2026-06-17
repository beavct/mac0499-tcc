MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito {nm_dist: 'Vila Sônia'})<-[:PARTE_DE*1..3]-(s:SetorCensitario)
MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_01_conv_05 = true

WITH m, d, sum(s.v0001) AS populacao_total, count(DISTINCT saude) AS unidades_internacao_publicas

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       populacao_total,
       unidades_internacao_publicas;
