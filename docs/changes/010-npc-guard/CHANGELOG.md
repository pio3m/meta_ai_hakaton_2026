# POC 04 — NPC Guard: changelog

Data: 2026-11-04. Status: implementacja i testy mock/API/przeglądarka zakończone.

## Dodano

- Lokalny Guard Buddy’ego: statusy ALLOWED / OUT_OF_SCOPE / BLOCKED, kod powodu i etap decyzji.
- Kontrolę jawnych prób nadpisywania instrukcji, ujawniania promptów, podszywania się pod role oraz prób związanych z sekretami i konfiguracją.
- Normalizację Unicode, diakrytyków i znaków niewidocznych oraz ograniczoną detekcję instrukcji zakodowanych Base64, URL, Unicode escape i ROT13.
- Lokalną odpowiedź w świecie Chess Corp dla rozpoznanych ataków i tematów spoza gry, bez wywołania dostawcy AI.
- Kontrolę odpowiedzi dostawcy przed dostarczeniem graczowi, w tym znanych fragmentów instrukcji i skonfigurowanych sekretów.
- Oddzielną, ograniczoną pamięć modelu, do której nie trafiają odrzucone tury. Widoczna historia gracza zachowuje odmowy.
- W Inspectorze: status i powód Guard, etap wejście/wyjście oraz osobną odpowiedź dostarczoną graczowi. Jury widzi wyłącznie bezpieczną odpowiedź własnej sesji.
- 81 dodatkowych testów i dowody przeglądarkowe.

## Zmieniono lub naprawiono

- Przeniesiono niezaufane teksty kontekstu z roli developer do osobnej wiadomości user z oznaczeniem danych. Instrukcja Buddy’ego pozostaje stała, a kontekst nadal opisuje questy.
- Wzmocniono dotychczasową instrukcję postaci bez dodatkowego LLM, endpointu moderacyjnego ani zależności.
- Rozszerzono maskowanie znanych sekretów w Inspectorze o standardową i URL-safe postać Base64.
- Klient rozpoznaje lokalną odpowiedź jako „Guard (lokalnie)”.
- Zachowano pierwszy quest, wszystkie typy Directora, zgodność planów v1/v2, grafiki, sterowanie i port 8080.

## Powiązania

- Przed rozpoczęciem POC 04 utworzono bezpieczny checkpoint POC 03.5: `ccb3af6`; kod działającego POC 03.5 jest w poprzednim `674eb7b`.
- Raport: [REPORT.md](REPORT.md).
- Zmiany POC 04 pozostawiono bez osobnego commita; prośba o commit dotyczyła stanu POC 03.5 przed rozpoczęciem prac.
