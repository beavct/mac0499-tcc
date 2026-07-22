MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(demo:PerfilDemografia)
WITH m, d, sum(coalesce(demo.v01031, 0)) AS populacao_infantil_distrito

MATCH (d)<-[:PARTE_DE*1..3]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.tp_dependencia = 4
  AND e.qt_tur_inf > 0
RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       e.id_aparelho AS id_escola,
       e.nm_aparelho AS nome_escola,
       populacao_infantil_distrito
ORDER BY populacao_infantil_distrito DESC, id_escola;