MATCH (m:Municipio)<-[:PARTE_DE]-(:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(demo:PerfilDemografia)
WITH m, sum(coalesce(demo.v01040, 0) + coalesce(demo.v01041, 0)) AS populacao_60_mais

OPTIONAL MATCH (m)<-[:PARTE_DE*1..4]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.tp_dependencia IN [1, 2, 3]
WITH m, populacao_60_mais, count(DISTINCT e) AS escolas_publicas
WHERE escolas_publicas > 0

OPTIONAL MATCH (m)<-[:PARTE_DE*1..4]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_02_conv_01 = true
WITH m, populacao_60_mais, escolas_publicas, count(DISTINCT saude) AS unidades_ambulatorial_sus

RETURN m.nm_mun AS municipio,
       escolas_publicas,
       unidades_ambulatorial_sus,
       populacao_60_mais,
       CASE WHEN unidades_ambulatorial_sus = 0 THEN null
            ELSE round(toFloat(escolas_publicas) / unidades_ambulatorial_sus, 2) END AS razao_escola_saude
ORDER BY razao_escola_saude DESC;