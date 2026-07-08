MATCH (s:SetorCensitario)-[:TEM_PERFIL]->(carac:PerfilDomiciliosParte1)
MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.tp_dependencia IN [1, 2, 3]
  AND coalesce(carac.v00006, 0) > 0
  AND NOT EXISTS {
      MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
      WHERE saude.at_02_conv_01 = true
  }
RETURN DISTINCT m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       s.cd_setor AS codigo_setor,
       coalesce(carac.v00006, 0) AS moradores_improvisados
ORDER BY moradores_improvisados DESC;
