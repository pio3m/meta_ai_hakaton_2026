# Rejestr dużych zmian

Każda duża zmiana otrzymuje nowy katalog `NNN-krotki-slug/`, a w nim osobne pliki:

- `CHANGELOG.md`: co dodano, zmieniono, naprawiono lub usunięto.
- `REPORT.md`: cel, zakres, wykonane testy z wynikami, uruchomienie, ograniczenia i następny krok.
- `evidence/`: opcjonalne zrzuty i materiały weryfikacyjne bez sekretów lub prywatnych rozmów.

Numer jest kolejny w całym projekcie. Nie nadpisujemy zakończonych kart, aby opisać następną zmianę. W trakcie pracy można aktualizować kartę bieżącej zmiany; późniejsza duża poprawka otrzymuje nowy numer. Małe poprawki dokumentujemy w nowym pliku `NNN-slug/updates/YYYY-MM-DD-krotki-opis.md` powiązanej zmiany, z opisem zmiany i wynikiem sprawdzenia. Jeśli nazwa jest zajęta, dodaj kolejny numer.

Zacznij od [szablonu changelogu](_template/CHANGELOG.md) i [szablonu raportu](_template/REPORT.md). Wyniki historyczne zawsze oznaczaj jako historyczne. Nie zapisuj kluczy API, tokenów dostępu, cookies ani prywatnych promptów.

| Nr | Zmiana | Changelog | Raport |
|---|---|---|---|
| 001 | POC 01 — grywalna ulica | [Zmiany](001-poc01/CHANGELOG.md) | [Raport](001-poc01/REPORT.md) |
| 002 | POC 02 — rozmowa z Buddy’m | [Zmiany](002-buddy-ai/CHANGELOG.md) | [Raport](002-buddy-ai/REPORT.md) |
| 003 | Pierwsze prawdziwe wywołanie Muse Spark | [Zmiany](003-meta-live/CHANGELOG.md) | [Raport](003-meta-live/REPORT.md) |
| 004 | AI Inspector i widok jury | [Zmiany](004-ai-inspector/CHANGELOG.md) | [Raport](004-ai-inspector/REPORT.md) |
| 005 | Organizacja dokumentacji zmian | [Zmiany](005-change-documentation/CHANGELOG.md) | [Raport](005-change-documentation/REPORT.md) |
| 006 | POC 03 — AI Game Director | [Zmiany](006-ai-game-director/CHANGELOG.md) | [Raport](006-ai-game-director/REPORT.md) |
| 007 | POC 03 — rzeczywisty Director Muse Spark | [Zmiany](007-director-meta-live/CHANGELOG.md) | [Raport](007-director-meta-live/REPORT.md) |
| 008 | POC 03.5 — dynamiczne questy i zagadki | [Zmiany](008-dynamic-quests-puzzles/CHANGELOG.md) | [Raport](008-dynamic-quests-puzzles/REPORT.md) |
| 009 | DirectorPlanV2 — kontrolowany test Muse Spark LIVE | [Zmiany](009-director-v2-meta-live/CHANGELOG.md) | [Raport](009-director-v2-meta-live/REPORT.md) |
