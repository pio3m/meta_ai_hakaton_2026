# POC 03.5 — Dynamic Quests & Puzzles: changelog

Data: 2026-11-02. Status: zakończona implementacja i weryfikacja mock.

## Dodano

- Schemat JSON wersji 2 z typami COLLECT, SEQUENCE i LOGIC_PUZZLE; jawny wybór parsera po wersji i dalszą obsługę istniejących planów wersji 1.
- SEQUENCE: trzy terminale A/B/C, zadana permutacja, deterministyczny postęp i zerowanie po błędzie.
- LOGIC_PUZZLE: trzy zamknięte szablony SUM, DIFFERENCE i NEXT_NUMBER, parametry w ograniczonym zakresie, pytanie i odpowiedź obliczane przez silnik.
- Numeryczne pole odpowiedzi: E otwiera terminal, cyfry wpisują, Backspace usuwa, Enter sprawdza, Esc zamyka; błędna odpowiedź nie zalicza zadania.
- Mock każdego typu, wybierany F4 przed ukończeniem pierwszego questu. R zachowuje wybrany wariant testowy przy nowej sesji.
- Trzecie zatwierdzone miejsce sceny: środek ulicy; walidację wszystkich obiektów i ich wzajemnych odstępów.
- W Inspectorze: typ questu oraz postęp, błędy, próby i wynik wykonania. Backend odtwarza ograniczony przebieg zdarzeń klienta tym samym silnikiem reguł.
- 43 nowe testy; dowody pełnego przejścia wszystkich trzech typów w przeglądarce.

## Zmieniono lub naprawiono

- Obecny adapter Meta wysyła schemat wersji 2; generacja i zapis wyniku nadal korzystają z dotychczasowych mechanizmów.
- Wspólne czyste reguły backendu i klienta znajdują się w `game/director_contract.py`; nie dodano osobnej architektury, zależności ani systemu pluginów.
- Uproszczono istniejący transport, usuwając nadpisaną, nieużywaną definicję funkcji; lista endpointów jawnie obejmuje nowy bezpłatny endpoint wykonania.
- Znak kolejności w HUD zmieniono na obsługiwane przez font `>`; pole rozwiązania przyjmuje wyłącznie cyfry, zgodnie z szablonami.
- Zachowano oryginalne grafiki, sterowanie WASD/E, pierwszy quest, jego nagrodę, rozmowy z Buddy’m, port 8080 i zabezpieczenia Inspectora.
- Nie wykonano płatnych wywołań Meta. Nie dodano Guarda, chodzących NPC ani audio.

## Powiązania

- Raport: [REPORT.md](REPORT.md).
- Nie wykonano commita.
