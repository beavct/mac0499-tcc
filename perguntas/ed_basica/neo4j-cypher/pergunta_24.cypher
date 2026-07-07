MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE s.situacao = 'Urbano'
  AND e.qt_tur_fund_int > 0
RETURN m.nm_mun AS municipio,
       sum(s.v0001) AS populacao_urbana_atendida_integral
ORDER BY populacao_urbana_atendida_integral DESC;
