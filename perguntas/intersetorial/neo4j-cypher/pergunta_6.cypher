MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDemografia)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
  AND (coalesce(p.v01019, 0) + coalesce(p.v01032, 0)) > 100

MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.qt_tur_eja_fund > 0 OR e.qt_tur_eja_med > 0

WITH m, d, s, (coalesce(p.v01019, 0) + coalesce(p.v01032, 0)) AS pop_idosa_70_mais
WHERE NOT (s)<-[:LOCALIZADA_EM]-(:EquipamentoSaude {at_03_conv_01: true})

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       s.cd_setor AS codigo_setor,
       pop_idosa_70_mais
ORDER BY pop_idosa_70_mais DESC;