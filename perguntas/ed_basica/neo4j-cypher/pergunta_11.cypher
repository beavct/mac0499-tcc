MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(a:PerfilAlfabetizacao)
MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
  AND e.qt_tur_med > 0
  AND e.qt_tur_bas_n > 0
WITH m, d, s, e, (coalesce(a.v00644, 0) - (coalesce(a.v00748, 0))) AS jovens_analfabetos
WHERE jovens_analfabetos > 0
RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       s.cd_setor AS codigo_setor, 
       e.id_aparelho AS id_escola, 
       e.nm_aparelho AS nome_escola, 
       jovens_analfabetos
ORDER BY jovens_analfabetos DESC;