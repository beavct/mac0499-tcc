MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(c:PerfilDomiciliosParte1)
MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.qt_tur_bas_ead > 0
RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       s.cd_setor AS codigo_setor, 
       e.id_aparelho AS id_escola, 
       e.nm_aparelho AS nome_escola,
       e.qt_tur_bas_ead AS turmas_ead,
       coalesce(c.v00078, 0) AS domicilios_mais_5_moradores
ORDER BY domicilios_mais_5_moradores DESC;
