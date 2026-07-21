MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito {nm_dist: 'Vila Sônia'})<-[:PARTE_DE*1..3]-(s:SetorCensitario)
WITH m, d, sum(coalesce(s.v0001, 0)) AS populacao_total

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_04_conv_01 = true
WITH m, d, populacao_total, count(DISTINCT saude) AS unidades_urgencia_sus

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       populacao_total,
       unidades_urgencia_sus;
