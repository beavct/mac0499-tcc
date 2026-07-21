MATCH (m:Municipio)<-[:PARTE_DE]-(:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(esc:Escola)
MATCH (s)-[:TEM_PERFIL]->(dom2:PerfilDomiciliosParte2)
WHERE esc.tp_dependencia IN [1, 2, 3]
  AND coalesce(dom2.v00401, 0) > 30
  AND NOT EXISTS {
      MATCH (vig:EquipamentoSaude)
      WHERE vig.at_06_conv_01 = true
        AND point.distance(esc.location, vig.location) <= 4000
  }
RETURN esc.id_aparelho AS id_escola,
       esc.nm_aparelho AS nome_escola,
       m.nm_mun AS municipio,
       coalesce(dom2.v00401, 0) AS domicilios_lixo_irregular_no_setor
ORDER BY domicilios_lixo_irregular_no_setor DESC;
