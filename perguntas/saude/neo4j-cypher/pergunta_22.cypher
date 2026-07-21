MATCH (m:Municipio)<-[:PARTE_DE*1..3]-(sd:Subdistrito)<-[:PARTE_DE*1..3]-(s:SetorCensitario)
OPTIONAL MATCH (s)<-[:LOCALIZADA_EM]-(saude:EquipamentoSaude)
WHERE saude.at_01_conv_01 = true
WITH m, sd, s, count(DISTINCT saude) AS leitos_no_setor
WITH m, sd, max(leitos_no_setor) AS max_leitos_setor, min(leitos_no_setor) AS min_leitos_setor
WHERE max_leitos_setor - min_leitos_setor > 0
RETURN m.nm_mun AS municipio,
       sd.cd_subdist AS subdistrito,
       max_leitos_setor - min_leitos_setor AS disparidade_leitos,
       max_leitos_setor,
       min_leitos_setor
ORDER BY disparidade_leitos DESC;
