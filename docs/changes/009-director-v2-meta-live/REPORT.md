# DirectorPlanV2 — raport kontrolowanego testu Meta Muse Spark

Data: 2026-11-02 (Europe/Warsaw). Status: zakończony powodzeniem. Jedyna zatwierdzona próba została wykorzystana; dalsze płatne wywołania Directora są wyłączone.

## Cel i wynik

Wykonano jeden rzeczywisty test schematu DirectorPlanV2 przy użyciu istniejącego adaptera i walidatorów. Model miał pełny wybór COLLECT / SEQUENCE / LOGIC_PUZZLE. Sam wybrał **COLLECT**, utworzył quest **„Pierwsze zlecenie kurierskie”**, zwrócił poprawny JSON wersji 2, a backend i klient przyjęły plan. Zadanie zostało ukończone klawiaturą w przeglądarce. Inspector pokazał rzeczywisty model, tokeny, pozytywną walidację i wynik `completed`.

Nie ponawiano generacji w celu uzyskania innego typu. Nie wymuszano typu, nie zastępowano odpowiedzi mockiem, nie poprawiano planu ręcznie ani nie zmieniano walidatora.

## Procedura i ochrona kosztów

1. Przeczytano AGENTS.md i sprawdzono istniejący adapter, prompt, kontrakt wersji 2 i endpoint wykonania.
2. Uruchomiono istniejący zestaw testów bez płatnych usług: **118 passed**, 20,95 s, jedno znane ostrzeżenie Starlette/TestClient dotyczące httpx/httpx2.
3. Uruchomiono izolowany Compose `chess-director-v2-live` pod `127.0.0.1:8081`, używając istniejących obrazów `chess-corp-backend` i `chess-corp-game` z `--no-build`. Nie przebudowywano gry. Początkowe przygotowanie wymagało wskazania istniejących nazw obrazów dla nowego projektu Compose; nie uruchomiło generacji ani połączenia z Meta.
4. Potwierdzono SHA256 pliku adaptera w użytym obrazie backendu względem bieżącego źródła. Produkcyjne źródła pozostały bez zmian.
5. Tymczasowy moduł startowy zastosował poprzednią procedurę LIVE: limit jednej próby na cały proces, zajmowany przed wywołaniem delegata. Delegat był rzeczywistym `MetaDirector`, a jego odpowiedź wracała bez podmiany.
6. W `finally` zamykano zgodę Directora i jego własnego adaptera HTTP niezależnie od powodzenia odpowiedzi i walidacji. Nie było automatycznych ponowień, restartowania procesu z nowym budżetem ani fallbacku do mocka.
7. Dodatkowo w izolowanej instancji zablokowano provider Buddy’ego, aby nawet przypadkowa rozmowa nie wykonała płatnego HTTP. Zwykły Buddy na 8080 zachował konfigurację Meta. W teście używano tylko skryptowych dialogów pierwszego questu, bez wiadomości do AI Buddy’ego.
8. Pierwszy quest przeszedł gracz: D do Buddy’ego, E/Enter, Esc, A do terminala, odbiór identyfikatora, D do Buddy’ego i zakończenie. To automatycznie wywołało jedyną generację Directora.

### Brak wymuszenia typu

Rzeczywisty payload w Inspectorze zawiera niezmieniony prompt „choose ONE quest_type: COLLECT, SEQUENCE or LOGIC_PUZZLE” i pełną enumerację tych trzech typów w JSON Schema. Kontekst wysłany do modelu nie zawiera ani żądanego `quest_type`, ani `mock_type`.

Nie naciskano F4. Widoczny przed generacją domyślny wariant mock COLLECT jest ustawieniem interfejsu testowego i nie trafia do payloadu Meta; istniejący adapter go ignoruje. Dowodem wyboru jest oryginalna odpowiedź modelu oraz sprawdzony rzeczywisty kontrakt wysłanego żądania, zapisane w eksporcie.

## Wynik API

| Parametr | Wynik |
|---|---|
| Rzeczywiste wywołania Directora | **1** |
| Wywołania Buddy’ego | **0** |
| Model odpowiedzi | `muse-spark-1.3` |
| HTTP Meta | **200** |
| Czas endpointu z generacją i walidacją | **1852,52 ms** |
| Tokeny wejściowe | **1023** |
| Tokeny wyjściowe | **361** |
| Tokeny razem | **1384** |
| Schemat odpowiedzi | `schema_version=2` |
| Wybrany typ | **COLLECT** |
| Backend | `valid=true`, `errors=[]` |
| Klient | Plan przyjęty, quest i obiekt widoczne; dostawca META |
| Wykonanie w Inspectorze | `status=completed`, `progress=1`, `mistakes=0`, `events=1` |

Pomiar czasu dotyczy endpointu, a nie wyłącznie czasu przetwarzania u dostawcy. Nie wyliczano ceny pieniężnej. Liczniki tokenów pochodzą z rzeczywistej odpowiedzi API.

### Wygenerowane zadanie

- Tytuł: „Pierwsze zlecenie kurierskie”.
- Cel: „Odnajdź i podnieś paczkę dyrektora”.
- Obiekt: `director_package`, „Pakunek dyrektora”, wygląd `data_chip`.
- Lokalizacja: `east_side`, rozwiązywana przez silnik do zatwierdzonego punktu [780,452].
- Warunek: `collect_object`, cel `director_package`.
- `sequence=[]`, `puzzle=null` — poprawne dla wybranego COLLECT.
- Komunikat ukończenia: „Dostarczono paczkę. Dobra robota pierwszego dnia.”

Gracz przeszedł w prawo i nacisnął E. Obiekt zniknął, HUD pokazał „UKOŃCZONE: Pierwsze zlecenie kurierskie”. Nie manipulowano stanem gry przez JavaScript ani API. Backend odtworzył zdarzenie klienta tym samym deterministycznym silnikiem i zaktualizował wpis Inspectora. Raportowanie wykonania nie wywołało LLM.

## Pięć wymaganych sprawdzeń

| Sprawdzenie | Wynik |
|---|---|
| Model sam wybiera typ | **Tak** — zaoferowano wszystkie trzy typy, wybrał COLLECT |
| Poprawny JSON v2 | **Tak** — odpowiedź zawiera wersję 2 i wymagane, spójne pola |
| Backend i klient akceptują plan | **Tak** — walidacja pozytywna, quest rzeczywiście pojawił się w grze |
| Quest można ukończyć klawiaturą | **Tak** — ruch D i zebranie E, potwierdzenie na HUD |
| Inspector: model, tokeny, walidacja i wykonanie | **Tak** — widok właściciela i bezpieczny eksport potwierdzają wszystkie pola |

## Dowody

- [Bezpieczny wynik JSON](evidence/live-result.json): surowa odpowiedź tekstowa modelu, JSON, zatwierdzony plan, model, tokeny, walidacja, wykonanie i zestaw typów rzeczywiście zaoferowanych modelowi. Bez klucza API, tokenu administracyjnego, cookies, identyfikatora sesji i prywatnej historii.
- [Quest aktywny](evidence/quest-v2-live-active.png).
- [Quest ukończony — pełny ekran](evidence/quest-v2-live-completed.png).
- [Quest ukończony — obszar gry](evidence/quest-v2-live-completed-canvas.png).
- [Inspector — model, tokeny i typ](evidence/inspector-v2-metrics.png).
- [Inspector — walidacja i wykonanie](evidence/inspector-v2-execution.png).
- [Blokada kosztów](evidence/cost-guard.txt).

Potwierdzono dokładnie jeden wpis generacji Directora, zero wpisów Buddy’ego i jeden komunikat blokady `attempted=1 paid_permission=false`. Nie wykonywano dodatkowego płatnego zapytania.

## Stan po teście

- `DIRECTOR_ALLOW_PAID_REQUESTS=false` jest jawnie zapisane w `.env` i potwierdzone przez `Settings.from_env()` w działającym zwykłym backendzie.
- Izolowana konfiguracja testowa również została zmieniona na false, a następnie kontenery i sieć testowa wyłączone przez Compose down. Port 8081 nie pozostaje uruchomiony.
- Zwykłe kontenery na 8080 pozostają healthy. Buddy: `meta`; Director: `mock`; zgoda Directora: `false`.
- Wpisy Inspectora są w RAM. Przed wyłączeniem testu wyeksportowano wynik i zapisano zrzuty. Nie przenoszono sztucznie wywołania LIVE do normalnego Inspectora na 8080.
- Nie zmieniono kodu gry, grafik, promptu ani schematu; nie dodano funkcjonalności. Nie wykonano commita.

Gra nadal działa pod http://localhost:8080, Inspector pod http://localhost:8080/admin. Zwykłe uruchomienie pozostaje `docker compose up -d`; do tego testu nie była potrzebna przebudowa obrazów.

## Ograniczenia i uwagi

- Wykonano jedną generację. **SEQUENCE i LOGIC_PUZZLE nie zostały sprawdzone z żywą odpowiedzią Meta w tym teście** — model nie wybrał ich, a nie ponawiano zapytania w celu zmiany typu. Ich wyniki mock opisuje raport 008.
- Jeden poprawny plan nie jest pomiarem niezawodności lub rozkładu wyborów modelu.
- Tekst fabularny opisuje przyniesienie paczki „do biura”, chociaż POC nie udostępnia wnętrza biura. Formalny cel i warunek są jednoznacznie COLLECT; HUD silnika wskazał zebranie obiektu i zadanie ukończyło się bez dodatkowej podróży. To drobna niespójność narracyjna, której nie poprawiano ani nie ukrywano przez podmianę odpowiedzi. Walidacja strukturalna nie ocenia całej semantyki opowieści.
- Wykonanie w Inspectorze oznacza odtworzenie zdarzeń klienta, nie autorytatywny serwer ruchu ani mechanizm antycheat.
- Nie wykonywano nowych testów grafik ani dodatkowego smoke Pygame w tym etapie bez zmian kodu; pełne uruchomienie klienta w przeglądarce i 118 testów wykonano rzeczywiście teraz. Wcześniejsze wyniki Pygame/mock są w raporcie 008.

## Następny najmniejszy krok

Dalszy test LIVE, także w celu pokrycia pozostałych typów, wymaga nowej osobnej zgody. Obecna próba jest zakończona i nie pozostawiła włączonej zgody płatnej.
