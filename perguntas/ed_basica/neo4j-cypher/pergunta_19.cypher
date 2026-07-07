MATCH (m:Municipio)<-[:PARTE_DE*1..3]-(sd:Subdistrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WITH m, sd, max(coalesce(e.qt_tur_inf, 0)) AS max_turmas, min(coalesce(e.qt_tur_inf, 0)) AS min_turmas

RETURN m.nm_mun AS municipio,
       sd.cd_subdist AS subdistrito,
       (max_turmas - min_turmas) AS disparidade_oferta_infantil
ORDER BY disparidade_oferta_infantil DESC;
