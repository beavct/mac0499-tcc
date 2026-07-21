MATCH (m:Municipio)<-[:PARTE_DE*1..3]-(b:Bairro)<-[:PARTE_DE*1..3]-(s:SetorCensitario)<-[:LOCALIZADA_EM]-(e:Escola)
WHERE e.qt_tur_inf_cre > 0

WITH DISTINCT m, b
WHERE NOT EXISTS {
    MATCH (b)<-[:PARTE_DE*1..3]-(:SetorCensitario)<-[:LOCALIZADA_EM]-(es:EquipamentoSaude)
    WHERE es.at_02_conv_01 = true
}

// Agrupa por nome do bairro: bairros homônimos em subdistritos diferentes são
// nós distintos no grafo, mas representam o mesmo bairro na visão do usuário.
RETURN DISTINCT m.nm_mun AS municipio,
       b.nm_bairro AS bairro
ORDER BY municipio, bairro;
