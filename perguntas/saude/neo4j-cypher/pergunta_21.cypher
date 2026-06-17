MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(a:PerfilAlfabetizacao)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
WITH m, d, s, a

OPTIONAL MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_06_conv_05 = true

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       sum(coalesce(a.v00901, 0)) AS analfabetos_15_mais,
       count(DISTINCT saude) AS unidades_vigilancia_publica
ORDER BY analfabetos_15_mais DESC;
