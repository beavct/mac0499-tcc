MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)-[:TEM_PERFIL]->(ent:PerfilEntornoDomicilios)
MATCH (s)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE (e.qt_tur_eja_fund > 0 OR e.qt_tur_eja_med > 0)
  AND coalesce(ent.v05013, 0) > 30
  AND NOT EXISTS {
      MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
      WHERE saude.at_04_conv_01 = true
  }
RETURN DISTINCT m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       s.cd_setor AS codigo_setor,
       coalesce(ent.v05013, 0) AS domicilios_sem_iluminacao
ORDER BY domicilios_sem_iluminacao DESC;
