MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDemografia)
MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_04_conv_01 = true
  AND (COALESCE(p.v01040, 0) + COALESCE(p.v01041,0)) > 0
RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       s.cd_setor AS codigo_setor, 
       saude.id_aparelho AS id_unidade, 
       saude.nm_aparelho AS nome_unidade, 
       (COALESCE(p.v01040, 0) + COALESCE(p.v01041,0)) AS idosos_60_mais
ORDER BY idosos_60_mais DESC;
