MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDomiciliosParte2)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
  AND coalesce(p.v00486, 0) = 0

MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_06_conv_01 = true

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       count(DISTINCT saude) AS vigilancia_saude_sus;
