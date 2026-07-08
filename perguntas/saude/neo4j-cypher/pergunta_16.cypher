MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(dom2:PerfilDomiciliosParte2)
WITH m, d,
     sum(coalesce(s.v0001, 0)) AS populacao_total,
     sum(coalesce(dom2.v00488, 0)) AS domicilios_fossa_rudimentar

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       populacao_total,
       domicilios_fossa_rudimentar,
       round(1000.0 * domicilios_fossa_rudimentar / populacao_total, 2) AS fossa_por_mil_habitantes
ORDER BY fossa_por_mil_habitantes DESC, domicilios_fossa_rudimentar DESC;
