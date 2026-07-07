MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDomiciliosParte2)
MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.tp_dependencia IN [1, 2, 3]
  AND e.qt_tur_med > 0
  AND e.qt_tur_bas_d > 0
  AND p.v00094 > 0

RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       s.cd_setor AS codigo_setor,
       e.id_aparelho AS id_escola, 
       e.nm_aparelho AS nome_escola,
       e.qt_tur_med AS turmas_ensino_medio,
       e.qt_tur_bas_d AS turmas_diurno,
       p.v00094 AS responsaveis_indigenas_casa
ORDER BY responsaveis_indigenas_casa DESC;