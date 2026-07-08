MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(dom2:PerfilDomiciliosParte2)
WITH m, d, sum(coalesce(dom2.v00094, 0)) AS responsaveis_indigenas

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.tp_dependencia IN [1, 2, 3]
  AND (e.qt_tur_fund_ai > 0 OR e.qt_tur_fund_af > 0)
WITH m, d, responsaveis_indigenas, count(DISTINCT e) AS escolas_fund_publicas

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_02_conv_01 = true
WITH m, d, responsaveis_indigenas, escolas_fund_publicas,
     count(DISTINCT saude) AS unidades_ambulatoriais_sus

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       responsaveis_indigenas,
       escolas_fund_publicas,
       unidades_ambulatoriais_sus
ORDER BY responsaveis_indigenas DESC;
