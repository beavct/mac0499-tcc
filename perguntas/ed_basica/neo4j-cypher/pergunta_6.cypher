MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilAlfabetizacao)
WHERE coalesce(p.v00901, 0) > 0
  AND NOT EXISTS { MATCH (s)<-[:LOCALIZADA_EM]-(:Escola) }

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       s.cd_setor AS codigo_setor,
       p.v00901 AS nao_alfabetizados
ORDER BY nao_alfabetizados DESC
LIMIT 20;