MATCH (m:Municipio {nm_mun: 'Campinas'})<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilParentesco)
WITH m, d, sum(coalesce(p.v01188, 0)) AS domicilios_chefia_feminina_sem_conjuge

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_01_conv_07 = true
WITH m, d, domicilios_chefia_feminina_sem_conjuge, count(DISTINCT saude) AS estabelecimentos_gratuidade

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       domicilios_chefia_feminina_sem_conjuge,
       estabelecimentos_gratuidade
ORDER BY domicilios_chefia_feminina_sem_conjuge DESC;
