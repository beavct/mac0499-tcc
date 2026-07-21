MATCH (sem:Escola)
WHERE sem.qt_tur_inf_cre = 0
  AND EXISTS {
      MATCH (com:Escola)
      WHERE com.qt_tur_inf_cre > 0
        AND com.id_aparelho <> sem.id_aparelho
        AND point.distance(sem.location, com.location) <= 2000
  }
RETURN sem.id_aparelho AS id_escola,
       sem.nm_aparelho AS nome_escola
ORDER BY nome_escola;
