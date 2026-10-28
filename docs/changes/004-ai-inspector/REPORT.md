# AI Inspector i widok jury — raport

Data zmiany: 28.10.2026.

Karta odtworzona 28.10.2026 na podstawie wcześniejszej dokumentacji i historii Git.

## Cel i zakres

Równoczesna prezentacja gry oraz podglądu pracy LLM, z oddzieleniem pełnego dostępu właściciela od ograniczonego widoku jury.

## Weryfikacja historyczna

- Testy bazowe: 38 passed; po zmianie: 50 passed.
- W przeglądarce sprawdzono logowanie, automatyczne odświeżanie, payload oraz izolację sesji jury.
- Testy przeglądarkowe działały na osobnym Compose w trybie mock na 8081.
- Właściwe środowisko zachowało port 8080 i tryb Meta; nie wykonywano nowych płatnych wywołań.
- Commit: `427b75d` — `Add secured AI Inspector with session-scoped jury view`.

## Materiały

- [Instrukcja, zabezpieczenia i pełny raport](../../AI_INSPECTOR.md)
- [Panel właściciela — mock](../../inspector_owner.png)
- [Widok jury — mock](../../inspector_jury.png)

## Ograniczenia

Bufor i sesje logowania znikają po restarcie. Tokeny są pokazywane tylko wtedy, gdy API je zwraca. Wyniki pochodzą z weryfikacji tej zmiany; nie powtarzano jej podczas tworzenia tej karty.
