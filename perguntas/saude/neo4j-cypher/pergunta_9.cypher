MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDemografia)
MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_06_conv_01 = true
  AND (coalesce(p.v01019, 0) + coalesce(p.v01032, 0)) > 0
RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       s.cd_setor AS codigo_setor, 
       saude.id_aparelho AS id_unidade, 
       saude.nm_aparelho AS nome_unidade, 
       (coalesce(p.v01019, 0) + coalesce(p.v01032, 0)) AS populacao_idosa_70_mais
ORDER BY populacao_idosa_70_mais DESC;
