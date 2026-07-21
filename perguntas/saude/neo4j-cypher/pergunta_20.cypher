MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(amb:EquipamentoSaude)
WHERE amb.at_02_conv_01 = true // Ambulatorial - SUS
WITH m, d, count(DISTINCT amb) AS ambulatorios_sus_no_distrito

MATCH (d)<-[:PARTE_DE*1..3]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(internacao:EquipamentoSaude)
WHERE internacao.at_01_conv_01 = true // Internação - SUS

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       internacao.id_aparelho AS id_unidade_internacao,
       internacao.nm_aparelho AS nome_unidade_internacao,
       ambulatorios_sus_no_distrito
ORDER BY ambulatorios_sus_no_distrito DESC, municipio, distrito;
