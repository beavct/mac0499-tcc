MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDomiciliosParte2)
MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.tp_dependencia IN [1, 2, 3]
  AND coalesce(p.v00495, 0) > 0
RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       s.cd_setor AS codigo_setor,
       count(DISTINCT e) AS escolas_sem_saneamento_entorno;
