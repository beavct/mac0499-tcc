// Nota de comparação com o PostgreSQL: 12 escolas a cerca de 5 km de uma unidade aparecem só
// aqui, porque o point.distance usa a fórmula de haversine e o SQL, a distância geodésica.
MATCH (esc:Escola)
WHERE NOT EXISTS {
    MATCH (vig:EquipamentoSaude)
    WHERE vig.at_06_conv_01 = true
      AND point.distance(esc.location, vig.location) <= 5000
}
MATCH (esc)-[:LOCALIZADA_EM]->(:SetorCensitario)-[:PARTE_DE*1..3]->(:Distrito)-[:PARTE_DE]->(m:Municipio)
RETURN m.nm_mun AS municipio,
       esc.id_aparelho AS id_escola,
       esc.nm_aparelho AS nome_escola;
