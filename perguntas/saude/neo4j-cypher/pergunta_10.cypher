MATCH (m:Municipio)<-[:PARTE_DE]-(d:Distrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)
WITH m, d, sum(s.v0001) AS total_habitantes
WHERE total_habitantes > 50000

OPTIONAL MATCH (d)<-[:PARTE_DE*1..3]-(s2:SetorCensitario)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_02_conv_01 = true
WITH m, d, total_habitantes, count(DISTINCT saude) AS qtd_ambulatorios_sus
WHERE qtd_ambulatorios_sus < 3

RETURN m.nm_mun AS municipio,
       d.nm_dist AS distrito,
       total_habitantes,
       qtd_ambulatorios_sus
ORDER BY total_habitantes DESC;
