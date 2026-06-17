MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE m.cd_mun IN ['3550308', '3509502', '3548708']
  AND s.situacao = 'Urbano'
  AND saude.at_02_conv_07 = true
RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       sum(s.v0001) AS populacao_urbana_gratuidade
ORDER BY populacao_urbana_gratuidade DESC;
