MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(com:Escola)
WHERE com.in_laboratorio_ciencias = true
WITH m, d, count(DISTINCT com) AS escolas_com_laboratorio
WHERE escolas_com_laboratorio >= 5

MATCH (d)<-[:PARTE_DE*1..3]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(sem:Escola)
WHERE sem.in_laboratorio_ciencias = false

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       escolas_com_laboratorio,
       sem.id_aparelho AS id_escola_sem_lab,
       sem.nm_aparelho AS nome_escola_sem_lab
ORDER BY escolas_com_laboratorio DESC, municipio, distrito;
