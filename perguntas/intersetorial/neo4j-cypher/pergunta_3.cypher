MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(ent:PerfilEntornoDomicilios)
WITH m, d,
     sum(coalesce(ent.v05007, 0)) AS dom_sem_pavimentacao,
     sum(coalesce(ent.v05022, 0)) AS dom_sem_calcada
WHERE dom_sem_pavimentacao > 1000 AND dom_sem_calcada > 1000

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.tp_dependencia IN [1, 2, 3] AND e.qt_tur_fund > 0
WITH m, d, dom_sem_pavimentacao, dom_sem_calcada, count(DISTINCT e) AS escolas_fund_publicas
WHERE escolas_fund_publicas > 5

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_04_conv_01 = true
WITH m, d, dom_sem_pavimentacao, dom_sem_calcada, escolas_fund_publicas,
     count(DISTINCT saude) AS unidades_urgencia_sus
WHERE unidades_urgencia_sus < 3

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       dom_sem_pavimentacao,
       dom_sem_calcada,
       escolas_fund_publicas,
       unidades_urgencia_sus
ORDER BY dom_sem_pavimentacao DESC;
