MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)
WHERE s.v0001 > 1000
  AND NOT (s)<-[:LOCALIZADA_EM]-(:EquipamentoSaude)
RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       s.cd_setor AS codigo_setor,
       s.v0001 AS total_moradores
ORDER BY total_moradores DESC;
