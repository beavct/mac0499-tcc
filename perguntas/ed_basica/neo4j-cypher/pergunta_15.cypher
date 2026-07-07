MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)

OPTIONAL MATCH (s)-[:PARTE_DE]->(b:Bairro)
WITH m, d, coalesce(b.nm_bairro, 'Não demarcado') AS bairro, s

MATCH (s)-[:TEM_PERFIL]->(p:PerfilParentesco)
WITH m, d, bairro, s, coalesce(p.v01215, 0) AS chefia_setor

OPTIONAL MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)
WITH m, d, bairro, s, chefia_setor, sum(coalesce(e.qt_tur_inf_cre_int, 0)) AS turmas_setor

RETURN m.nm_mun AS municipio, 
       d.nm_dist AS distrito,
       bairro, 
       sum(chefia_setor) AS chefia_feminina_unipessoal, 
       sum(turmas_setor) AS turmas_creche_integral
ORDER BY chefia_feminina_unipessoal DESC;