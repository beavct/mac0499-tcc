MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDomiciliosParte1)
MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE (e.qt_tur_fund_ai > 0 OR e.qt_tur_fund_af > 0 OR e.qt_tur_fund > 0)
  AND p.v00006 > 50
RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       s.cd_setor AS codigo_setor,
       e.id_aparelho AS id_escola,
       e.nm_aparelho AS nome_escola,
       p.v00006 AS moradores_dom_improvisados
ORDER BY moradores_dom_improvisados DESC;
