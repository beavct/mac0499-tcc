MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
WITH m, d, max(coalesce(e.qt_tur_inf, 0)) AS max_turmas, min(coalesce(e.qt_tur_inf, 0)) AS min_turmas

RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       (max_turmas - min_turmas) AS disparidade_oferta_infantil
ORDER BY disparidade_oferta_infantil DESC;