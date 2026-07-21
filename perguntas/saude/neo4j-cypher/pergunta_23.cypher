MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(r:PerfilRacaCor)
WITH m, d, sum(coalesce(r.v01389, 0)) AS populacao_amarela

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_01_conv_07 = true

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       populacao_amarela,
       count(DISTINCT saude) AS leitos_gratuitos
ORDER BY populacao_amarela DESC;
