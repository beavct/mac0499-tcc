// Vizinho mais próximo: para cada unidade de Diagnose e Terapia (SADT) SUS,
// a unidade de Urgência SUS mais próxima.
//
// Nota de comparação com o PostgreSQL: 4 unidades SADT do estado têm coordenadas do CNES que
// não caem em nenhum setor censitário e não são carregadas no grafo; a versão SQL também as
// exclui, pelo mesmo ST_Contains do ETL. A unidade de Urgência mais próxima ainda difere em
// cerca de 130 casos, porque o point.distance do Neo4j usa a fórmula de haversine e o SQL, a
// distância geodésica (nenhuma unidade de Urgência SUS fica fora dos setores).
MATCH (diag:EquipamentoSaude)
WHERE diag.at_03_conv_01 = true
CALL (diag) {
    MATCH (urg:EquipamentoSaude)
    WHERE urg.at_04_conv_01 = true AND urg.id_aparelho <> diag.id_aparelho
    RETURN urg AS u, point.distance(diag.location, urg.location) AS d
    ORDER BY d
    LIMIT 1
}
MATCH (diag)-[:LOCALIZADA_EM]->(:SetorCensitario)-[:PARTE_DE*1..3]->(:Distrito)-[:PARTE_DE]->(m:Municipio)
RETURN m.nm_mun AS municipio,
       diag.id_aparelho AS id_diagnose,
       diag.nm_aparelho AS nome_diagnose,
       u.id_aparelho AS id_urgencia_proxima,
       u.nm_aparelho AS nome_urgencia_proxima,
       round(d, 1) AS distancia_m;
