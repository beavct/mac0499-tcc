MATCH (m:Municipio)<-[:PARTE_DE*1..3]-(b:Bairro)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.qt_tur_inf_cre > 0

WITH m, b, collect(DISTINCT s) AS setores_com_creche

UNWIND setores_com_creche AS s
OPTIONAL MATCH (s)<-[:LOCALIZADA_EM]-(es:EquipamentoSaude)
WHERE es.at_02_conv_01 = true

WITH m, b, count(DISTINCT es) AS saude_ambulatorial_sus
WHERE saude_ambulatorial_sus = 0

RETURN m.nm_mun AS municipio,
       b.nm_bairro AS bairro
ORDER BY municipio, bairro;