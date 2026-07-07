MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)

WITH m.nm_mun AS municipio, e.tp_dependencia AS rede, count(DISTINCT e) AS qtd_escolas

WITH municipio, collect({rede: rede, qtd: qtd_escolas}) AS redes,
     sum(qtd_escolas) AS total_municipio

UNWIND redes AS r
RETURN municipio,
       CASE r.rede
         WHEN 1 THEN 'Federal'
         WHEN 2 THEN 'Estadual'
         WHEN 3 THEN 'Municipal'
         WHEN 4 THEN 'Privada'
         ELSE 'Não Informado'
       END AS dependencia_adm,
       r.qtd AS qtd_escolas,
       round((r.qtd * 100.0) / total_municipio, 2) AS percentual_no_municipio
ORDER BY municipio, dependencia_adm;