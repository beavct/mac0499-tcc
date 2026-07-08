MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(ef:Escola)
WHERE ef.qt_tur_fund > 0
WITH m, d, count(DISTINCT ef) AS escolas_fundamental_no_distrito

MATCH (d)<-[:PARTE_DE*1..3]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(em:Escola)
WHERE em.qt_tur_med > 0

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       em.id_aparelho AS id_escola_em,
       em.nm_aparelho AS nome_escola_em,
       escolas_fundamental_no_distrito
ORDER BY escolas_fundamental_no_distrito DESC, municipio, distrito;
