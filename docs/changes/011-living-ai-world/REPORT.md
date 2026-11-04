# Living AI World — raport końcowy

Data: 2026-11-04. Status: zakończony działający POC; test LIVE zamknięty po trzech płatnych wywołaniach.

## Cel i wynik

Na dotychczasowej ulicy Chess Corp działają czterej widoczni, animowani NPC: Buddy, Security, Hacker i Employee. Spacerują bez ruchu gracza, patrolują, podchodzą do terminali, rozmawiają i reagują na gracza. Muse Spark 1.3 rzeczywiście wygenerował trzy poprawne plany zachowań dla wszystkich czterech postaci. Silnik zaakceptował je i wykonywał w przeglądarce. Nie podstawiano mocka zamiast odpowiedzi modelu.

Świat lokalny działa od pierwszej klatki. Każda postać ma osobowość, pozycję, stan akcji, cel, nastrój oraz pamięć sześciu ostatnich wydarzeń. Wspólny dziennik jest ograniczony do 12 zdarzeń; do modelu trafia ostatnich osiem. Model otrzymuje aktualne pozycje, stan pierwszego questu, cele, profile i pamięć. Nie otrzymuje kluczy, historii prywatnych rozmów Buddy’ego ani prawa do wykonywania kodu.

## Implementacja

- `content/world_ai.json`: cztery profile, kolory, prędkości i dziewięć zatwierdzonych lokalizacji, w tym dwa terminale.
- `game/world_contract.py`: zamknięty słownik JSON i walidacja współdzielona z backendem. Sześć akcji: MOVE_TO, PATROL, WAIT, TALK_TO, INSPECT_TERMINAL i REACT_TO_PLAYER. Dokładnie cztery unikalne postacie, 1–3 akcje na każdą, ograniczone teksty i czas 2–15 s. Nieznane pola, pozycje, cele, akcje, duplikaty i niepoprawne wersje są odrzucane.
- `game/living_world.py`: deterministyczny ruch, kolejki akcji, limity czasu, rozmowy, pamięć, reakcje na E i odległość gracza, asynchroniczny transport oraz telemetria. Buddy zostaje przy posterunku przed końcem pierwszego questu i zatrzymuje się na czas rozmowy.
- `backend/world_models.py`, `world_ai.py`, `world_routes.py`: Pydantic, istniejący adapter Meta, wspólne planowanie czterech NPC jednym wywołaniem, budżet i idempotencja rund. Endpointy `/api/world/plan` i `/api/world/execution`.
- Istniejący Inspector: osobny typ World AI, rzeczywisty payload i JSON właściciela, wynik walidacji, model, tokeny, opóźnienie, cele i źródła działań, błędy oraz telemetria wykonania. Zakończone akcje pozostają zapisane przy wywołaniu mimo kolejnych aktualizacji stanu NPC.
- Nowe źródła są oznaczane META / MOCK / FALLBACK. Lokalne potwierdzenia rozmowy i reakcje na E mają własne oznaczenie FALLBACK, nawet jeśli poprzedni plan pochodził z Meta. Odtworzenie odpowiedzi z cache jest oznaczane w HUD.
- Nie dodano nowych usług, frameworków ani baz. Compose nadal wystawia grę na 8080 i używa jednego procesu backendu. Buddy chat, NPC Guard i questy pozostają w dotychczasowych modułach.

## Grafiki i interfejs

Wykorzystano istniejące cztery klatki `assets/processed/player_0..3.png` (72×90, RGBA) pochodzące z oryginalnych zasobów. Role rozróżniają kolory i podpisy: Buddy turkusowy, Security zielony, Hacker różowy, Employee złoty. Tła, font i oryginały w `grafika/` nie zostały zmienione. Dodano prosty terminal danych, panel stanów czterech postaci, dymki oraz komunikaty z oznaczeniem źródła. Poprawiono dopasowanie canvas do okna, aby runtime nie zmniejszał gry do kwadratowego pola z szarym tłem.

## Koszty i procedura LIVE

Test odbył się w izolowanym Compose na porcie 8082, z Buddy i Game Directorem w trybie mock oraz ich płatnymi zgodami wyłączonymi. World AI miał osobną zgodę, limit trzech wywołań globalnie i na sesję, odstęp 30 s, maksymalnie 1800 tokenów wyjściowych i budżet 50000 tokenów. Dodatkowa tymczasowa osłona testowa dopuszczała najwyżej trzy rzeczywiste próby i po trzeciej wyłączała zgodę adaptera. Nie zmieniała promptów ani odpowiedzi modelu.

| Rzeczywiste wywołanie | Model | Czas | Tokeny wejście / wyjście / razem | Walidacja |
|---|---|---:|---:|---|
| 1 | muse-spark-1.3 | 11144,58 ms | 1514 / 1235 / 2749 | poprawny JSON, backend i klient zaakceptowały |
| 2 | muse-spark-1.3 | 7106,30 ms | 1768 / 894 / 2662 | poprawny JSON, backend i klient zaakceptowały |
| 3 | muse-spark-1.3 | 6368,42 ms | 1514 / 650 / 2164 | poprawny JSON, backend i klient zaakceptowały |

**Razem: 3 płatne World AI, 7575 tokenów; 0 płatnych Buddy i 0 Game Director.** Wszystkie rzeczywiste odpowiedzi miały HTTP 200. Były również bezkosztowe żądania zablokowane przez budżet: jedno na granicy minimalnego odstępu oraz jedno po zamknięciu zgody, po resecie gry. Nie były to wywołania Meta. Ponowne otwarcie ostatniej sesji demonstracyjnej korzystało z cache, bez kolejnej generacji.

Wybrane przez model zachowania:

- Buddy: powitanie gracza przez REACT_TO_PLAYER oraz później WAIT przy posterunku.
- Security: MOVE_TO do centrum, TALK_TO do Employee, następnie PATROL centrum/brama i rozmowa z Hackerem. W kolejnej odpowiedzi zmienił nastrój na suspicious.
- Hacker: MOVE_TO do terminala identyfikatorów i INSPECT_TERMINAL, rozmowa z Employee oraz wycofanie do west_corner.
- Employee: WAIT, rozmowa z Security i REACT_TO_PLAYER z prośbą o docenienie raportu.

Model sam wybrał **wszystkie sześć** typów akcji w trzech odpowiedziach. Zapisana telemetria LIVE potwierdza zakończenie MOVE_TO, TALK_TO, INSPECT_TERMINAL i WAIT. Ruch PATROL był widoczny z etykietą META. Nie deklarujemy zapisanej kompletnej telemetrii ukończenia wszystkich sześciu w LIVE: w pierwszej wersji podglądu najstarsze zakończenia znikały po przejściu do lokalnych zachowań; zostało to naprawione po teście i objęte testem regresyjnym.

Dwie akcje pierwszego planu zakończyły się jawnym `expired`: dalekie MOVE_TO Hackera i reakcja Buddy’ego spoza wcześniejszego zasięgu rozmowy. Silnik nie teleportował NPC i nie deklarował sukcesu. Po teście zwiększono zasięg REACT_TO_PLAYER, aby Buddy mógł przywitać stojącego na starcie gracza bez opuszczania miejsca pierwszego questu; poprawkę sprawdzono bez nowego wywołania Meta.

Po błędzie granicznym odstępu zmieniono planowanie klienta na zegar rzeczywisty i dodano jedną sekundę marginesu. Nie wykonywano dodatkowych płatnych testów tych poprawek. Trzecie wywołanie wykorzystało już klienta z poprawionym zegarem, ale limit globalny po nim zatrzymał kolejne generacje; odstęp dwóch kolejnych rund poprawionego klienta potwierdza test automatyczny.

Po teście kontenery LIVE zostały zatrzymane i usunięte; tymczasowy plik Compose zawierający konfigurację klucza został usunięty. Lokalny `.env` ma **WORLD_AI_MODE=mock** i **WORLD_AI_ALLOW_PAID_REQUESTS=false**. Zachowano wcześniejsze ustawienia integracji Buddy’ego i Game Directora użytkownika.

## Weryfikacja wykonana w tym etapie

| Sprawdzenie | Wynik |
|---|---|
| Testy przed zmianą | 199 passed |
| Końcowe `.venv\Scripts\python.exe -m pytest -q` | 233 passed, 1 istniejące ostrzeżenie Starlette/httpx; 36,32 s |
| 34 nowe scenariusze World AI | kontrakt obu stron, sześć akcji, ruch czterech NPC, pamięć, atomiczne odrzucenie planu, ograniczenie Buddy’ego, zgody, brak klucza, budżet, odstęp, limity między sesjami, błędy, idempotencja, fake HTTP, telemetry i izolacja jury — przechodzą |
| Pygame `main.py --smoke`, SDL dummy, World network=false | wyrenderowano 12 klatek |
| Symulacja lokalna bez sieci | wszystkie cztery NPC zmieniły pozycję; sześć akcji można zakończyć deterministycznie |
| Docker / pygbag | końcowa budowa udana; obraz Linux/Python 3.12, pygbag 0.9.3 i oryginalny pygame WASM |
| Pierwszy quest w przeglądarce | rozmowa → identyfikator → powrót do Buddy’ego, ukończony przy działających NPC |
| COLLECT w przeglądarce, mock | ukończony klawiaturą |
| SEQUENCE w przeglądarce, mock | ukończony klawiaturą, C → A → B |
| LOGIC_PUZZLE w przeglądarce, mock | ukończony klawiaturą, ciąg 3,7,11, odpowiedź 15 |
| Buddy chat i NPC Guard w przeglądarce, mock | pytanie o awans otrzymuje odpowiedź z kontekstem zakończonej zagadki; próba ujawnienia promptu dostaje lokalną odmowę |
| Inspector w przeglądarce | widoczny typ World AI, model, tokeny, czas, JSON i walidacja; widok jury pokazuje tylko jego sesję |
| Końcowe HTTP na 8080 | `/`, `/health`, `/web_app.apk` i skrypt Inspectora: HTTP 200; oba kontenery healthy |
| Retencja wykonania w końcowym Inspectorze | trzy rundy mock zachowały po 12 zakończonych akcji, bieżące stany mają jawne źródła; 0 płatnych wywołań głównej wersji podczas sprawdzenia |
| Sekrety i grafiki | skan zmienionych plików pod kątem rzeczywistych skonfigurowanych kluczy/tokenów: czysto; `.env` ignorowany, brak zmian oryginalnych i przetworzonych grafik |
| `git diff --check` | bez błędów whitespace |

Dowody znajdują się w `evidence/`: `live-results.json` zawiera wyłącznie wybrane pola wyników testowych, bez kluczy, tokenów logowania, pełnych promptów i prywatnych rozmów. Zrzuty `live-world.png`, `live-inspector-jury.png`, `mock-collect-completed.png`, `mock-sequence-completed.png`, `mock-logic-completed.png`, `mock-guard-blocked.png`, `local-world.png` i `final-pygame-smoke.png` dokumentują poszczególne sprawdzenia. `final-world-8080.png` pokazuje końcową wersję po aktualizacji głównego Compose.

## Uruchomienie i prezentacja

1. W katalogu projektu uruchom `docker compose up --build -d`.
2. Otwórz http://localhost:8080 w nowej karcie i kliknij Graj. Czterech NPC działa od razu. WASD / E / Enter / Esc / R pozostają bez zmian. F4 nadal wybiera mock typu questu przed końcem pierwszego zadania.
3. W drugim oknie otwórz http://localhost:8080/admin i zaloguj się istniejącym ADMIN_TOKEN. Właściciel widzi rzeczywisty prompt; dla jury utwórz sesję demonstracyjną i użyj jej linku gry oraz `/admin/jury` w osobnym profilu/incognito z tokenem jury.
4. Aby uruchomić nową, płatną prezentację świata, ustaw w `.env` WORLD_AI_MODE=meta, WORLD_AI_ALLOW_PAID_REQUESTS=true, pozostaw limity 3/3 i model muse-spark-1.3 oraz istniejący MODEL_API_KEY. Dla kosztów wyłącznie World AI ustaw Buddy i Director na mock i wyłącz ich płatne zgody. Pełny przykład jest w README.
5. Po zmianie konfiguracji wykonaj `docker compose up -d --force-recreate backend game`, otwórz nową kartę. Po trzech płatnych próbach dalszy świat działa lokalnie. Po prezentacji przywróć World mock/false i ponownie odtwórz kontenery.
6. Lokalnie bez sieci, PowerShell: `$env:CHESS_CORP_WORLD_NETWORK='false'`, następnie `.venv\Scripts\python.exe main.py`. W WSL można użyć `CHESS_CORP_WORLD_NETWORK=false uv run python main.py` z WSLg; sam WSLg nie był odrębnie testowany w tym etapie. Przeglądarka przez Docker Desktop/WSL nadal korzysta z portu 8080.

## Ograniczenia

- To POC: proste barwione postacie współdzielą oryginalne klatki i mogą minąć się lub wizualnie nałożyć. Nie ma pathfindingu, kolizji NPC między sobą, walki ani audio.
- Zatwierdzony plan nie gwarantuje osiągnięcia odległego celu w krótkim czasie. Timeout jest normalnym, jawnym wynikiem wykonania.
- Po wyczerpaniu kolejki NPC przechodzi do jawnie lokalnego zachowania. Stary cel i pamięć pozostają kontekstem kolejnej decyzji modelu.
- Domyślnie trzy generacje na sesję oraz trzy globalnie, a nie nieskończona symulacja płatna. Limity globalne i historia Inspectora są w RAM jednego procesu; restart backendu je zeruje. Nie uruchamiać wielu workerów dla wspólnego budżetu.
- Budżet tokenów jest konserwatywnym limitem aplikacji, nie rozliczeniem kwotowym dostawcy. Brak usage nie zwalnia rezerwacji.
- Telemetria jest raportem klienta, weryfikowanym względem dozwolonych akcji planu; nie jest niezależną serwerową symulacją świata ani dowodem odpornym na oszustwa.
- Świat używa istniejącego timeoutu Meta, do 25 s. Animacje i lokalny fallback działają w czasie oczekiwania. Runtime Python/WASM przy pierwszym uruchomieniu przeglądarki nadal wymaga Internetu.
- Nie wykonano dodatkowego płatnego testu końcowych drobnych poprawek. Potwierdzono je testami lokalnymi, mock API oraz przeglądarką.

## Następny najmniejszy krok

Przed wystąpieniem włączyć World META na jedną ograniczoną sesję demonstracyjną i przygotować grę oraz widok jury w dwóch oknach. Rozbudowa architektury nie jest potrzebna.
