MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDemografia)
WHERE coalesce(p.v01041, 0) > 100

MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.qt_tur_eja_fund > 0 OR e.qt_tur_eja_med > 0

WITH m, d, s, coalesce(p.v01041, 0) AS pop_idosa_70_mais
WHERE NOT (s)<-[:LOCALIZADA_EM]-(:EquipamentoSaude {at_04_conv_01: true})

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       s.cd_setor AS codigo_setor,
       pop_idosa_70_mais
ORDER BY pop_idosa_70_mais DESC;