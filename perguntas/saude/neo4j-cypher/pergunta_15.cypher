MATCH (m:Municipio)<-[:PARTE_DE*1..3]-(b:Bairro)<-[:PARTE_DE]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDomiciliosParte2)
WITH m, b, sum(coalesce(p.v00093, 0)) AS pop_bairro_no

OPTIONAL MATCH (b)<-[:PARTE_DE]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_03_conv_06 = true

WITH m, b, pop_bairro_no, count(DISTINCT saude) AS urg_bairro_no

RETURN m.nm_mun AS municipio,
       b.nm_bairro AS bairro,
       sum(pop_bairro_no) AS responsaveis_raca_amarela,
       sum(urg_bairro_no) AS urgencia_privada
ORDER BY responsaveis_raca_amarela DESC;
