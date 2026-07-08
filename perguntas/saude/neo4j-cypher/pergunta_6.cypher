MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(demo:PerfilDemografia)
WHERE (coalesce(demo.v01019, 0) + coalesce(demo.v01032, 0)) > 50
  AND NOT EXISTS {
      MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
      WHERE saude.at_03_conv_01 = true
  }
RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       s.cd_setor AS codigo_setor,
       (coalesce(demo.v01019, 0) + coalesce(demo.v01032, 0)) AS idosos_80_mais
ORDER BY idosos_80_mais DESC;
