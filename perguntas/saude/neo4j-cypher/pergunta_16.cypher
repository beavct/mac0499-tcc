MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE]-(b:Bairro)<-[:PARTE_DE]-(s:SetorCensitario)-[:TEM_PERFIL]->(c:PerfilDomiciliosParte1)
MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_06_conv_06 = true
RETURN m.nm_mun AS municipio, 
       b.nm_bairro AS bairro, 
       saude.id_aparelho AS id_unidade, 
       saude.nm_aparelho AS nome_unidade, 
       sum(coalesce(c.v00085, 0)) AS moradores_casa_vila
ORDER BY moradores_casa_vila DESC;
