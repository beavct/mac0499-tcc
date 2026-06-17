MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
  AND e.in_esgoto_rede_publica = false
  AND e.in_esgoto_fossa = false
RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       s.cd_setor AS codigo_setor,
       e.id_aparelho AS id_escola,
       e.nm_aparelho AS nome_escola
ORDER BY municipio, distrito, nome_escola;