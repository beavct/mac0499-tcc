MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDomiciliosParte2)
MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
  AND saude.at_03_conv_07 = true
RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       s.cd_setor AS codigo_setor, 
       p.v00488 AS domicilios_fossa_rudimentar,
       count(DISTINCT saude) AS unidades_urgencia_outros
ORDER BY domicilios_fossa_rudimentar DESC;
