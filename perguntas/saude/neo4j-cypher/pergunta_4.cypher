MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDemografia)
MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_02_conv_06 = true
  AND p.v01020 > 0
RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       saude.id_aparelho AS id_unidade, 
       saude.nm_aparelho AS nome_unidade, 
       p.v01020 AS pop_infantil_feminina
ORDER BY pop_infantil_feminina DESC;
