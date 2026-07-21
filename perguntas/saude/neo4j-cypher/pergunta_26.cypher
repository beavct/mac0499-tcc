// Vizinho mais próximo: para cada unidade de Diagnose e Terapia (SADT) SUS,
// a unidade de Urgência SUS mais próxima.
//
// Nota de comparação com o PostgreSQL: 4 unidades SADT do estado (em Lorena,
// Mongaguá, Monteiro Lobato e Santa Fé do Sul) têm coordenadas do CNES que não
// caem dentro de nenhum polígono de setor censitário, então o ETL (que ancora
// cada equipamento no setor que o contém, via ST_Contains) não as carrega como
// nós. Por isso elas não aparecem aqui, mas aparecem na versão PostgreSQL, que
// mede distância entre pontos sem depender do setor. A origem é a qualidade da
// coordenada na fonte, não a formulação da consulta.
MATCH (diag:EquipamentoSaude)
WHERE diag.at_03_conv_01 = true
CALL (diag) {
    MATCH (urg:EquipamentoSaude)
    WHERE urg.at_04_conv_01 = true AND urg.id_aparelho <> diag.id_aparelho
    RETURN urg AS u, point.distance(diag.location, urg.location) AS d
    ORDER BY d
    LIMIT 1
}
RETURN diag.id_aparelho AS id_diagnose,
       diag.nm_aparelho AS nome_diagnose,
       u.id_aparelho AS id_urgencia_proxima,
       u.nm_aparelho AS nome_urgencia_proxima,
       round(d, 1) AS distancia_m
ORDER BY distancia_m DESC;
