MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(p:PerfilDomiciliosParte2)
WHERE coalesce(p.v00111, 0) = 0

OPTIONAL MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_02_conv_05 = true

WITH m.nm_mun AS municipio, d.nm_dist AS distrito, s.cd_setor AS codigo_setor,
     count(DISTINCT saude) AS ambulatorios_especializados_publicos
WHERE ambulatorios_especializados_publicos > 0

RETURN municipio, distrito, codigo_setor, ambulatorios_especializados_publicos;
