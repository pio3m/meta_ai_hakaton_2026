# Zmiany 019 — lokalizacja EN/PL

- Wspólny katalog tłumaczeń prezentacji gry i AI Inspectora; EN jako domyślny język gry i jury, PL jako domyślny język właściciela.
- Dyskretny wybór EN/PL oraz skrót F2. Preferencja przeglądarki zachowana po odświeżeniu, niezależna od stanu świata.
- Lokalizacja HUD, sterowania, dialogów fabularnych, lokacji, mapy, Nyx, kontraktów, walki, dziennika, questów i zagadek.
- Język żądania w istniejących promptach Buddy/NPC, Quest Directora, zleceń sesji i World AI. Schematy planów, identyfikatory, walidacja i reguły wykonania bez zmian.
- Mock dwóch zleceń sesji pozwala sprawdzić cały obieg bez zgody na opłaty i bez modelu.
- Osobne preferencje języka panelu właściciela i jury. Karty NPC, stany i znane teksty silnika lokalizowane przy prezentacji.
- Wyniki AI i historia rozmów zachowują język źródłowy. Obce i nieustalone językowo dane są jawnie oznaczone jako oryginał; surowe JSON-y nie są tłumaczone.
- Testy izolowane od kluczy API, produkcyjnych woluminów i liczników kosztów. Audio i mechaniki pozostają bez zmian.
