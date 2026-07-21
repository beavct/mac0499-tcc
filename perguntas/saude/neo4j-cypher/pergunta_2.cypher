MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(a:PerfilAlfabetizacao)
MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_02_conv_01 = true
WITH m, d, s, saude, (coalesce(a.v00644, 0) - coalesce(a.v00748, 0)) AS jovens_analfabetos
WHERE jovens_analfabetos > 0
RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       s.cd_setor AS codigo_setor, 
       saude.id_aparelho AS id_unidade, 
       saude.nm_aparelho AS nome_unidade, 
       jovens_analfabetos
ORDER BY jovens_analfabetos DESC;
