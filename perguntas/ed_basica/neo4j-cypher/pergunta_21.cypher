MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(c:PerfilDomiciliosParte1)
MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.tp_dependencia = 2
  AND e.qt_tur_eja_fund > 0
  AND c.v00050 > 0
RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       s.cd_setor AS codigo_setor, 
       e.id_aparelho AS id_escola, 
       e.nm_aparelho AS nome_escola, 
       e.qt_tur_eja_fund AS turmas_eja_fundamental,
       c.v00050 AS moradores_cortico
ORDER BY moradores_cortico DESC;
