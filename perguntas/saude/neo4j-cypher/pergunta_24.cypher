MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDomiciliosParte2)
MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_06_conv_01 = true AND coalesce(p.v00316, 0) > 0
RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       s.cd_setor AS codigo_setor,
       coalesce(p.v00316, 0) AS domicilios_esgoto_inexistente,
       count(DISTINCT saude) AS unidades_vigilancia_sus
ORDER BY domicilios_esgoto_inexistente DESC;
