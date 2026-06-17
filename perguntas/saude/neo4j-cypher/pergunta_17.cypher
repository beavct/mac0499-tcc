MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(r:PerfilRacaCor)
MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
  AND saude.at_03_conv_05 = true

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       s.cd_setor AS codigo_setor,
       r.v01320 AS populacao_parda,
       count(DISTINCT saude) AS urgencias_publicas
ORDER BY populacao_parda DESC;
