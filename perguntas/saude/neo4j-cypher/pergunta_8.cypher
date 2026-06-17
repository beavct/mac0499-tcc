MATCH (m:Municipio {nm_mun: 'Campinas'})<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE]-(b:Bairro)<-[:PARTE_DE]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilParentesco)
WITH m, b, sum(coalesce(p.v01215, 0)) AS domicilios_unipessoais_femininos

OPTIONAL MATCH (b)<-[:PARTE_DE]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_01_conv_07 = true

RETURN m.nm_mun AS municipio, 
       b.nm_bairro AS bairro, 
       domicilios_unipessoais_femininos, 
       count(DISTINCT saude) AS estabelecimentos_gratuidade
ORDER BY domicilios_unipessoais_femininos DESC;
