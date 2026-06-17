MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDomiciliosParte2)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
  AND p.v00094 > 0

MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.tp_dependencia IN [1, 2, 3]
  AND (e.qt_tur_fund_ai > 0 OR e.qt_tur_fund_af > 0)

MATCH (s)<-[:LOCALIZADA_EM]-(es:EquipamentoSaude)
WHERE es.at_05_conv_01 = true

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       s.cd_setor AS codigo_setor,
       p.v00094 AS responsaveis_indigenas,
       count(DISTINCT e) AS escolas_fund_publicas,
       count(DISTINCT es) AS saude_outros_sus
ORDER BY responsaveis_indigenas DESC;