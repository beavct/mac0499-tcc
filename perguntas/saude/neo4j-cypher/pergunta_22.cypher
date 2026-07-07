MATCH (m:Municipio)<-[:PARTE_DE*1..3]-(sd:Subdistrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_01_conv_01 = true
RETURN m.nm_mun AS municipio,
       sd.cd_subdist AS subdistrito,
       count(DISTINCT saude) AS total_hospitais_internacao
ORDER BY total_hospitais_internacao DESC;
