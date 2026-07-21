MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.qt_tur_med > 0
WITH m, d, collect(DISTINCT e) AS escolas_em
WHERE size(escolas_em) = 1

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       escolas_em[0].id_aparelho AS id_escola,
       escolas_em[0].nm_aparelho AS nome_escola
ORDER BY municipio, distrito;
