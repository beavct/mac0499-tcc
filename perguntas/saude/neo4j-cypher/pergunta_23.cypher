MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(r:PerfilRacaCor)
MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
  AND saude.at_01_conv_07 = true

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       sum(coalesce(r.v01319, 0)) AS populacao_amarela,
       count(DISTINCT saude) AS leitos_gratuitos
ORDER BY populacao_amarela DESC;
