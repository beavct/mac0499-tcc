MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(c:PerfilDomiciliosParte1)
WHERE c.v00006 > 100
  AND NOT (s)<-[:LOCALIZADA_EM]-(:Escola)
  AND NOT (s)<-[:LOCALIZADA_EM]-(:EquipamentoSaude)

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       s.cd_setor AS codigo_setor,
       c.v00006 AS moradores_dom_improvisados
ORDER BY moradores_dom_improvisados DESC;