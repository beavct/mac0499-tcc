MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDomiciliosParte3)
MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
  AND saude.at_01_conv_06 = true
  AND p.v00498 > 100
RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       s.cd_setor AS codigo_setor, 
       saude.id_aparelho AS id_unidade, 
       saude.nm_aparelho AS nome_unidade, 
       p.v00498 AS moradores_apartamento
ORDER BY moradores_apartamento DESC;
