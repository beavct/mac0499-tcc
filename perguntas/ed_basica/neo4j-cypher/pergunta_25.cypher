// Multi-hop: percorre distrito → setores → escolas COM quadra, e depois
// volta pro mesmo distrito pra achar escolas SEM quadra (travessia lateral)
MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s1:SetorCensitario)<-[:LOCALIZADA_EM]-(e_com:Escola)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
  AND (e_com.in_quadra_esportes_coberta = true OR e_com.in_quadra_esportes_descoberta = true)
WITH m, d, count(DISTINCT e_com) AS escolas_com_quadra
WHERE escolas_com_quadra >= 5

MATCH (d)<-[:PARTE_DE*1..3]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(e_sem:Escola)
WHERE e_sem.in_quadra_esportes_coberta = false
  AND e_sem.in_quadra_esportes_descoberta = false

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       escolas_com_quadra,
       count(DISTINCT e_sem) AS escolas_sem_quadra,
       e_sem.id_aparelho AS id_escola_sem_quadra,
       e_sem.nm_aparelho AS nome_escola_sem_quadra
ORDER BY escolas_sem_quadra DESC;