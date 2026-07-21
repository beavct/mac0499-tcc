MATCH (m:Municipio)<-[:PARTE_DE]-(:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(urg:EquipamentoSaude)
MATCH (s)-[:TEM_PERFIL]->(par:PerfilParentesco)
WHERE urg.at_04_conv_01 = true
  AND coalesce(par.v01068, 0) > 80
  AND NOT EXISTS {
      MATCH (outra:EquipamentoSaude)
      WHERE outra.at_04_conv_01 = true
        AND outra.id_aparelho <> urg.id_aparelho
        AND point.distance(urg.location, outra.location) <= 10000
  }
RETURN urg.id_aparelho AS id_urgencia,
       urg.nm_aparelho AS nome_urgencia,
       m.nm_mun AS municipio,
       coalesce(par.v01068, 0) AS responsaveis_60_mais_no_setor
ORDER BY responsaveis_60_mais_no_setor DESC;
