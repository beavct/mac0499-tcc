MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(demo:PerfilDemografia)
MATCH (esc:Escola)-[:LOCALIZADA_EM]->(s)
WHERE esc.qt_tur_inf > 0
  AND coalesce(demo.v01031, 0) > 100
  AND NOT EXISTS {
      MATCH (outra:Escola)
      WHERE outra.qt_tur_inf > 0
        AND outra.id_aparelho <> esc.id_aparelho
        AND point.distance(esc.location, outra.location) <= 3000
  }
RETURN esc.id_aparelho AS id_escola,
       esc.nm_aparelho AS nome_escola,
       m.nm_mun AS municipio,
       coalesce(demo.v01031, 0) AS criancas_0_4_no_setor
ORDER BY criancas_0_4_no_setor DESC;
