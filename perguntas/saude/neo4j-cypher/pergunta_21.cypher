MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(a:PerfilAlfabetizacao)
WITH m, sum(coalesce(a.v00901, 0)) AS analfabetos_15_mais

OPTIONAL MATCH (m)<-[:PARTE_DE*1..4]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_06_conv_05 = true

RETURN m.nm_mun AS municipio,
       analfabetos_15_mais,
       count(DISTINCT saude) AS unidades_vigilancia_publica
ORDER BY analfabetos_15_mais DESC;
