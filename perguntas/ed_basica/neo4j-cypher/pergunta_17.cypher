MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(c:PerfilDomiciliosParte1)
MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.qt_tur_med > 0
RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       s.cd_setor AS codigo_setor, 
       coalesce(c.v00085, 0) AS moradores_casa_vila_condominio,
       count(DISTINCT e) AS qtd_escolas_medio
ORDER BY moradores_casa_vila_condominio DESC;
