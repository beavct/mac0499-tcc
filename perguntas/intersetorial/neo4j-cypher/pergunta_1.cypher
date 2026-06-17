MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
  AND e.tp_dependencia IN [1, 2, 3]
  AND NOT (s)<-[:LOCALIZADA_EM]-(:EquipamentoSaude {at_02_conv_01: true})

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       s.cd_setor AS codigo_setor,
       count(DISTINCT e) AS escolas_publicas
ORDER BY escolas_publicas DESC;