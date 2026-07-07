MATCH (m:Municipio)<-[:PARTE_DE*1..3]-(b:Bairro)<-[:PARTE_DE]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDomiciliosParte2)
MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_03_conv_06 = true

RETURN m.nm_mun AS municipio,
       b.nm_bairro AS bairro,
       sum(coalesce(p.v00093, 0)) AS responsaveis_raca_amarela,
       count(DISTINCT saude) AS urgencia_privada
ORDER BY responsaveis_raca_amarela DESC;
