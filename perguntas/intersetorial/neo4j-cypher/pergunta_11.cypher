MATCH (esc:Escola)
WHERE NOT EXISTS {
    MATCH (vig:EquipamentoSaude)
    WHERE vig.at_06_conv_01 = true
      AND point.distance(esc.location, vig.location) <= 5000
}
RETURN esc.id_aparelho AS id_escola,
       esc.nm_aparelho AS nome_escola
ORDER BY nome_escola;
