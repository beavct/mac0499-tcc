MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.qt_tur_inf_cre > 0
  AND e.qt_tur_med > 0
RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito, 
       s.cd_setor AS codigo_setor,
       e.id_aparelho AS id_escola, 
       e.nm_aparelho AS nome_escola,
       e.qt_tur_inf_cre AS qtd_turmas_creche,
       e.qt_tur_med AS qtd_turmas_medio
ORDER BY municipio, distrito, nome_escola;