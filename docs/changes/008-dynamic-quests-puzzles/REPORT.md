# POC 03.5 — raport Dynamic Quests & Puzzles

Data: 2026-11-02. Status: implementacja zakończona, trzy typy ukończone w przeglądarce w trybie mock. Bez nowych płatnych wywołań Meta.

## Cel i wynik

Rozszerzono istniejącego Directora o SEQUENCE oraz LOGIC_PUZZLE, zachowując COLLECT. Zachowano pierwszy quest, oryginalne grafiki, ruch gracza, działanie rozmów z Buddy’m oraz architekturę FastAPI/Pygame/pygbag. Nowa generacja używa wersji schematu 2; istniejące plany wersji 1 pozostają obsługiwane jako COLLECT.

**Rzeczywiście ukończone w przeglądarce:** COLLECT, SEQUENCE i LOGIC_PUZZLE. Każdy był uruchomiony po ponownym, pełnym przejściu pierwszego questu klawiaturą. Były to odpowiedzi mock, a nie nowe odpowiedzi prawdziwego Muse Spark. Adapter i prompt wersji 2 są przygotowane, ale ich płatnego wywołania nie wykonywano.

## Implementacja

### Kontrakt i zgodność

`backend/director_models.py` zachowuje `DirectorPlan` dla wersji 1 i dodaje `DirectorPlanV2`. Parser sprawdza rzeczywisty typ liczbowy wersji, jawnie wybiera model 1/2 i odrzuca nieznane wersje. Dane nie są wykonywane jako kod.

Wersja 2 zawiera wymagane pola: `schema_version`, `quest_type`, `create_quest`, `place_objects`, `sequence`, `puzzle`. Dodatkowe pola są zakazane. Typ i parametry muszą być spójne:

- COLLECT: jeden `director_package`, wygląd `data_chip`, warunek `collect_object`; pusta sekwencja i `puzzle=null`.
- SEQUENCE: dokładnie trzy różne ID `terminal_a/b/c`, wygląd `terminal`, trzy różne zatwierdzone miejsca i permutacja tych samych trzech ID. Warunek `activate_sequence`.
- LOGIC_PUZZLE: jeden `puzzle_terminal`, wygląd `terminal`, pusta sekwencja, jeden zatwierdzony szablon; warunek `solve_puzzle`.

Wspólny identyfikator zadania `director_delivery` pozostał dla zgodności sesji i kontekstu Buddy’ego; typ określa pole `quest_type`. Walidacja sprawdza liczbę obiektów, ID, referencje, typ ukończenia, długości i znaki tekstów, brak obcych działań oraz spójność parametrów. Schemat Meta ma zamknięte obiekty i wszystkie pola wymagane; nie zawiera `oneOf` ani `allOf`.

`game/director_contract.py` to niewielki moduł czystych funkcji współdzielonych przez klienta i API: walidacja, pozycje obiektów, pytania, obliczenie odpowiedzi i deterministyczne przejścia stanu. Nie importuje Pydantic, FastAPI ani Pygame, dlatego działa także w WASM. Backend Docker otrzymuje tylko ten moduł obok istniejącego kodu backendu i danych.

### Dozwolone miejsca i grafiki

`content/director_rules.json` zachowuje `west_side=[100,452]` i `east_side=[780,452]`, dodaje `center_side=[385,452]`. Model wybiera nazwę miejsca, nie dowolne współrzędne. Wersja 1 nadal dopuszcza tylko stare dwa miejsca.

Wszystkie obiekty są w obszarze ruchu, poza blokadami i z odstępem od Buddy’ego, terminala identyfikatora oraz pozostałych nowych interakcji. Promień wynosi 52. Nie modyfikowano `content/scene.json`, oryginałów `grafika/` ani przetworzonych grafik. Ponownie potwierdzono 476 plików oryginalnych zasobów; wcześniejsza inwentaryzacja rozmiarów, alfa i cięcia pozostaje w `docs/ASSET_REPORT.md`. Nowe terminale są prostymi prostokątami Pygame w istniejącej turkusowo-złotej palecie.

### Zasady rozgrywki

- **SEQUENCE:** HUD pokazuje rzeczywistą kolejność silnika i postęp 0..3. E przy właściwym terminalu zwiększa postęp. Każdy niewłaściwy terminal, także powtórzony już zatwierdzony, zeruje całą kolejność i zwiększa licznik błędów. Nie ma kary w ekwipunku ani pytania do LLM. Zaliczenie jest jednokrotne.
- **LOGIC_PUZZLE:** AI personalizuje tekst fabularny i wybiera parametry, ale nie podaje dowolnej odpowiedzi, wyrażenia ani funkcji do wykonania. Dokładne pytanie konstruuje silnik. SUM: `a+b`; DIFFERENCE: `a-b` z `a>=b`; NEXT_NUMBER: ciąg `a,a+b,a+2b`, jawnie stały przyrost, wynik `a+3b`. `a` jest liczbą całkowitą 1..20, `b` 1..9. Wszystkie wyniki są jednoznacznymi liczbami nieujemnymi.
- Odpowiedź jest sprawdzana lokalnie, bez LLM. Silnik akceptuje równoważny zapis liczby z zerami wiodącymi i spacjami zewnętrznymi na poziomie kontraktu. Interfejs przyjmuje cyfry ASCII, do 32 znaków; litery nie trafiają do pola. Błędna liczba pozwala ponowić próbę. Esc zamyka terminal bez utraty stanu, R poza polem rozpoczyna nową sesję.
- **COLLECT:** dotychczasowy zasięg E, pojedyncze zebranie i ukończenie, także dla starego planu 1.
- Pierwszy quest i jego identyfikator/nagroda pozostają niezależne. Nowe zadania nie przyznają ponownie starej nagrody.

### Inspector i wykonanie

Dotychczasowy `POST /api/director` generuje i waliduje plan. Nowy `POST /api/director/execution` nie wywołuje modelu: przyjmuje do 100 zdarzeń tej samej sesji i tego samego `call_id`, sprawdza niezmienność poprzedniego prefiksu i odtwarza przebieg czystymi regułami. Sprawdza obiekty, deklarowany zasięg i pozycję, kolejność oraz rozwiązania. Zmiana już zapisanej historii jest odrzucana; identyczny przebieg jest idempotentny.

Klient wysyła kolejne, uporządkowane migawki przebiegu w tle. Nie blokuje klatek oczekiwaniem na API. Wynik lokalnej rozgrywki nie jest zależny od oceny LLM ani od dodatkowego płatnego żądania.

Inspector nadal przechowuje ostatnie 200 **generacji** w RAM; interakcje aktualizują wpis generacji, zamiast zapełniać ten bufor. Pokazuje `quest_type`, plan, walidację i `execution`: status, postęp, liczbę błędów/prób/zdarzeń oraz źródło `client_events_replayed`. To jawnie oznaczona rekonstrukcja zdarzeń klienta, nie dowód autorytatywnego serwera ruchu ani mechanizm antycheat.

Pełne prompty nadal wymagają logowania właściciela. Jury otrzymuje tylko zatwierdzony plan i wynik własnej sesji demonstracyjnej. Nie udostępnia się surowych wpisanych odpowiedzi ani całego śladu interakcji. Cofnięcie dostępu i filtrowanie sesji są objęte testem.

## Weryfikacja automatyczna

| Faktycznie wykonane sprawdzenie | Wynik |
|---|---|
| Testy bazowe przed zmianami | 75 passed, 18,52 s |
| Ostateczne `.venv\Scripts\python.exe -m pytest -q` | **118 passed**, 25,31 s; 1 znane ostrzeżenie Starlette/TestClient o przyszłej migracji httpx na httpx2 |
| Zamknięty kontrakt v2 po stronie API i klienta | Wszystkie typy poprawne; odrzucanie nadmiarowych pól, niedozwolonych akcji/miejsc/wyglądów, błędnych warunków, duplikatów ID i miejsc |
| SEQUENCE | Wszystkie 6 permutacji, błąd po częściowym postępie, reset, poprawne zakończenie i brak ponownego zaliczenia |
| LOGIC_PUZZLE | Wszystkie dozwolone parametry trzech szablonów: 504 kombinacje; błędna odpowiedź, poprawna odpowiedź, jednoznaczna normalizacja liczb |
| Zgodność v1 | Dotychczasowe testy planów 1, klienta i adaptera; nowy test starego planu przez endpoint generacji i wykonania |
| Integracja API → klient → wykonanie → Inspector | Wszystkie trzy typy, błędne próby, stan completed, jedna nagroda pierwszego questu |
| Bezpieczeństwo raportowania | Obca sesja 404, modyfikacja prefiksu 409, zły zasięg/pola 422; brak modyfikacji zaakceptowanego wyniku po błędzie |
| Jury | Własna sesja, poprawne liczniki, brak cudzych wywołań, surowych odpowiedzi i pełnych promptów; cofnięcie tokenu |
| Pygame, SDL dummy, `main.py --smoke` | **12 klatek**, kod 0; nowy zrzut w bieżącym evidence, historyczny `docs/smoke.png` przywrócony |
| Docker Compose / pygbag | Budowa i start poprawne; Python 3.12 w kontenerze, pygbag 0.9.3, pakiet pygame WASM z kontrolą SHA256 |
| `git diff --check` | Bez błędów; wyłącznie komunikaty o normalizacji CRLF/LF |

Nowe testy znajdują się w `tests/test_director_v2.py`. Pozostawiono poprzednie testy i raporty. Nie dodawano zależności ani płatnych usług.

## Rzeczywiste testy przeglądarkowe

Testy prowadzono w przeglądarce wbudowanej, przez izolowany Compose na localhost:8081, z Buddy i Directorem w mocku, sztucznym kluczem oraz obiema zgodami płatnymi false. Stan gry nie był ustawiany przez JavaScript ani ręcznie przez API; wszystkie ruchy i interakcje wykonano klawiaturą.

| Typ | Rzeczywiście ukończony? | Obserwacja |
|---|---|---|
| COLLECT | **Tak** | Pierwszy quest → nośnik po lewej → E → ukończenie; Inspector completed, 1 zdarzenie |
| SEQUENCE | **Tak** | Pierwszy quest → B zamiast C → reset; C, C → ponowny reset; C, A, B → ukończenie. Inspector: 6 prób, 2 błędy, postęp 3/3 |
| LOGIC_PUZZLE | **Tak** | Pierwszy quest → terminal po prawej → pytanie o 3,7,11,? przy stałym przyroście → błędne 0 → poprawne 15 → ukończenie |
| LOGIC_PUZZLE po poprawce pola | **Tak, ponownie** | Zamknięcie Esc i ponowne otwarcie E, potwierdzenie wpisanej liczby na ekranie przed Enter. Inspector: 2 próby, 1 błąd, completed |

Test ujawnił nieobsługiwany przez font znak strzałki — zastąpiono go `>`. Po szybkim otwieraniu terminala i wysyłaniu tekstu sprawdzono dokładny wpis przed zatwierdzeniem. Pole ograniczono do cyfr, by znak E i inne litery nie mogły trafić do odpowiedzi; przypadek `e15x` objęto testem. W pierwszym przebiegu zagadki zapisano 3 próby i 2 odrzucone odpowiedzi; nie ukryto tego w eksporcie. Po poprawce i ponownym przejściu od początku potwierdzono 2 próby z jednym błędem.

Dowody:

- [COLLECT ukończony](evidence/collect-completed.png).
- [Błędny terminal](evidence/sequence-wrong.png), [reset po częściowym postępie](evidence/sequence-reset.png), [SEQUENCE ukończony](evidence/sequence-completed.png).
- [Pytanie](evidence/puzzle-question.png), [błędna odpowiedź](evidence/puzzle-wrong.png), [LOGIC_PUZZLE ukończony](evidence/puzzle-completed.png), [ponowne ukończenie po poprawce](evidence/puzzle-fixed-completed.png).
- [Inspector: walidacja i wykonanie](evidence/inspector-execution.png).
- [Wyniki wszystkich trzech przejść](evidence/browser-results.json), [wynik powtórki zagadki](evidence/puzzle-fixed-result.json), [Pygame start](evidence/pygame-start.png).

Dodatkowo na gotowej instancji **localhost:8080** ponownie ukończono pierwszy quest oraz SEQUENCE (C > A > B). Potwierdzono poprawione znaki kolejności i wynik completed w Inspectorze. [Aktywny quest](evidence/localhost8080-sequence-active.png), [ukończenie](evidence/localhost8080-sequence-completed.png), [obszar gry](evidence/localhost8080-completed-canvas.png), [wynik backendu](evidence/localhost8080-result.json).

Izolowane kontenery 8081 wyłączono po zapisaniu dowodów; gotowa instancja 8080 pozostaje uruchomiona. Bieżące wpisy Inspectora na 8081 zniknęły wraz z restartem/zamknięciem procesu, zgodnie z jego pamięciowym charakterem.

## Uruchomienie i użycie

```powershell
cd C:\Users\piotr\projects\hakaton_meta\chess-corp-poc-codex
docker compose up --build -d
```

WSL:

```bash
cd /mnt/c/Users/piotr/projects/hakaton_meta/chess-corp-poc-codex
docker compose up --build -d
```

1. Otwórz http://localhost:8080 w nowej karcie po zamknięciu starej. Zaczekaj na runtime i kliknij Graj.
2. **Przed ukończeniem pierwszego questu** wybierz F4: COLLECT → SEQUENCE → LOGIC_PUZZLE → COLLECT. Wybór jest widoczny pod HUD. Dotyczy tylko mocka; prawdziwy model wybiera typ sam.
3. Przejdź zwykły pierwszy quest: Buddy → terminal identyfikatora → Buddy. Po dialogach zamknij rozmowę Esc.
4. COLLECT: idź do wskazanego nośnika i E. SEQUENCE: idź do terminali A/B/C i naciskaj E w kolejności HUD. LOGIC_PUZZLE: E przy terminalu, wpisz cyfry, Enter sprawdza, Backspace poprawia, Esc zamyka.
5. R poza dialogiem/polem odpowiedzi rozpoczyna nową sesję; zachowuje wariant mock. Można następnie zmienić go F4. G ponawia tylko nieudaną generację, nie jest potrzebne do błędnej próby sekwencji lub zagadki.
6. http://localhost:8080/admin: istniejący ADMIN_TOKEN, potem typ planu, walidacja i wykonanie. Jury używa dotychczasowej wydzielonej sesji demo.

Desktop: uruchom backend Compose, `uv sync --locked`, następnie `uv run python main.py`. Natywny klient domyślnie używa backendu http://127.0.0.1:8080. Sam statyczny serwer HTTP bez FastAPI nie obsłuży Directora ani raportowania.

Końcowa instancja 8080 zachowuje Buddy `meta`, Director `mock`, `DIRECTOR_ALLOW_PAID_REQUESTS=false`. Zmiana nie włącza żadnej nowej zgody na płatne wywołania. Nie wysyłano wiadomości do prawdziwego Buddy’ego w czasie tych testów.

## Ograniczenia

- Jeden dynamiczny quest na sesję po pierwszym dniu, bez łańcucha wielu zadań; żeby wybrać kolejny wariant, użyj R i F4.
- Trzy sprawdzalne szablony numeryczne, a nie dowolne łamigłówki językowe. AI personalizuje fabułę i parametry; dokładne pytanie oraz odpowiedź należą do silnika.
- Walidacja nie ocenia jakości fabuły. Zaufany HUD silnika pokazuje faktyczną kolejność i miejsce niezależnie od tekstu modelu.
- Limit 100 prób/zdarzeń na zadanie. Dane, historia i Inspector są w RAM i znikają po restarcie; nie dodano trwałego zapisu.
- Wynik Inspector pochodzi z odtworzenia zdarzeń klienta. Sprawdzane są reguły i deklarowany zasięg, ale klient POC nie jest autorytatywnym serwerem ruchu ani systemem antycheat. Brak sieci nie cofa lokalnego ukończenia; raportowanie może wtedy pozostać nieaktualne.
- Wersja 2 adaptera Meta nie była wywołana na żywym API. Wynik poprzedniego testu wersji 1 znajduje się w raporcie 007 i nie jest wynikiem tego etapu.
- Brak Guarda, spacerujących NPC i audio. Oryginalne grafiki i kadrowanie pozostały bez zmian.

## Następny najmniejszy krok

Po osobnej zgodzie na koszt wykonać jedną kontrolowaną generację Muse Spark w schemacie 2 i przejść wybrany przez model typ zadania. Obecna zgoda Directora pozostaje wyłączona.
