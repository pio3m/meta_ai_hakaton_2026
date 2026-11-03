# POC 03 — raport AI Game Director

Data: 2026-10-28. Status: grywalny scenariusz mock ukończony; adapter Muse Spark gotowy i przetestowany na sztucznym HTTP. Prawdziwa generacja questów przez Meta nie została wywołana z uwagi na brak zgody na dodatkowe koszty.

## Cel i wynik

Po ukończeniu pierwszego questu gra automatycznie prosi Directora o jeden plan. Plan tworzy zadanie odzyskania nośnika i umieszcza obiekt w jednym z dwóch zatwierdzonych miejsc ulicy. Gracz podchodzi i naciska E. Silnik sprawdza odległość, stan zadania i posiadanie identyfikatora; usuwa obiekt i oznacza drugie zadanie jako ukończone. Potwierdzono pełne przejście obu questów klawiaturą w przeglądarce, bez ustawiania stanu gry przez narzędzia.

**Ważne rozróżnienie:** działający scenariusz testowy otrzymuje plan od mocka. Prawdziwy Muse Spark korzysta z tego samego kontraktu i walidatora, ale jego nowa odpowiedź dla Directora nie została jeszcze sprawdzona na żywym API. Nie przedstawiam symulacji jako prawdziwej generacji LLM.

## Implementacja

- `backend/director_models.py`: ścisłe modele Pydantic z zakazem dodatkowych pól, zamkniętymi typami akcji, identyfikatorami, wyglądem obiektu i warunkiem ukończenia. Odrzucane są kod zamiast JSON, bloki Markdown, duplikaty kluczy, nieznane akcje, pola pozycji/NPC, błędne referencje, teksty poza limitem i znaki sterujące. Wersja musi być liczbą całkowitą 1, a nie wartością logiczną.
- `backend/director.py`: osobny mock i adapter Meta używający istniejącego `MetaProvider.complete`. Prompt zawiera dozwolone działania, kontekst oraz miejsca. `response_format=json_schema` przekazuje pełny schemat do modelu. Mechanika nie polega na samym zapewnieniu modelu: odpowiedź zawsze sprawdza serwer i klient.
- `content/director_rules.json`: `east_side=[780,452]`, `west_side=[100,452]`, zasięg 52; koordynaty pochodzą z aplikacji, model wybiera tylko nazwę miejsca. Miejsca są w obszarze ruchu i nie kolidują z interakcjami Buddy’ego oraz terminala.
- `backend/director_routes.py`: `POST /api/director` wymaga ukończenia pierwszego questu i identyfikatora w kontekście. Klient ponownie sprawdza te warunki na własnym rzeczywistym stanie. Blokada sesji serializuje żądania; jeden zatwierdzony plan jest zwracany ponownie z cache. Błąd również zostaje zapamiętany; dopiero jawne ponowienie G pozwala wykonać kolejną próbę. Timeout i brak dostępu do API nie blokują ruchu ani starego questu.
- `game/director.py`: walidator bez Pydantic i innych zależności backendowych, zgodny z WASM. Plan jest stosowany w całości dopiero po walidacji. Zbieranie działa lokalnie i deterministycznie, bez drugiego pytania do LLM. Wielokrotne E nie powiela zdarzenia, nie przyznaje ponownie identyfikatora ani nagrody pierwszego dnia. Zaufana wskazówka silnika pokazuje stronę ulicy niezależnie od tekstu wygenerowanego przez model.
- `main.py`, transport Pygame/JS i modele kontekstu Buddy’ego: nowe zadanie i rozmowy współistnieją; NPC otrzymuje tytuł, cel i status aktywnego/ukończonego zadania. Model nie zmienia ekwipunku ani postępu.
- Inspector zachowuje wspólny bufor ostatnich 200 wywołań w RAM, rzeczywisty payload w miejscu HTTP, czas, model, tokeny i błędy. Dodano typ wywołania, JSON i walidację z etapem błędu. Właściciel widzi surową odpowiedź, jury tylko zatwierdzony plan własnej sesji; nie otrzymuje pełnego promptu, surowego odrzuconego JSON ani cudzej historii. Maskowanie sekretów i dotychczasowe logowanie pozostają aktywne.

## Grafiki

Zachowano istniejące pochodne oryginalnych zasobów użytkownika i wcześniejszy sposób kadrowania. Inwentaryzacja 476 plików pozostaje w `docs/ASSET_REPORT.md`. Nie zmieniano `grafika/` ani plików istniejących grafik. Nośnik danych jest małym placeholderem Pygame w turkusowo-złotej palecie gry, bez generowania obrazów i kosztów API.

## Weryfikacja

| Sprawdzenie wykonane w tym etapie | Wynik |
|---|---|
| Testy istniejącego projektu przed zmianami | 50 passed; punkt odniesienia tego etapu |
| `.venv\Scripts\python.exe -m pytest -q` po implementacji | 75 passed; jedno ostrzeżenie Starlette o przyszłej migracji TestClient z httpx na httpx2 |
| Testy schematu i reguł sceny | Oba miejsca poprawne; odrzucanie kodu, nadmiarowych pól, błędnych akcji, warunków, typów, długości, blokad i duplikatów kluczy |
| Testy endpointu i Inspector | Warunki startu, cache sukcesu/błędu, jawne ponowienie, jedna generacja przy równoległych żądaniach, timeout, autoryzacja i ograniczenie jury |
| Integracja gry z rzeczywistym endpointem FastAPI i mockiem | Pierwszy quest → plan → obiekt → zebranie → drugie ukończenie; jedna stara nagroda, brak podwójnego zebrania |
| Adapter Meta przez `httpx.MockTransport` | Schemat JSON w żądaniu, odczyt modelu/tokenów i ślad Inspector; bez połączenia z Meta |
| Brak osobnej zgody dla Directora | Próba Meta odrzucona przed wysłaniem HTTP |
| Pygame: `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`, `python main.py --smoke` | 12 wyrenderowanych klatek, kod 0; Python 3.13.3 / pygame-ce 2.5.8 |
| Docker Compose i pygbag | Budowa kod 0, Linux/Python 3.12, pygbag 0.9.3; lokalny pakiet Pygame/WASM z kontrolą SHA256 |
| Przeglądarka, izolowany Compose na 8081 | Pełne przejście pierwszego questu WASD/E/Enter, nowy quest mock, nośnik po lewej, zebranie E i komunikat drugiego ukończenia |
| Przeglądarka, Buddy po ukończeniu drugiego questu | Wysłanie syntetycznej wiadomości, odpowiedź mock, brak regresji interfejsu |
| Przeglądarka, `/admin` | Logowanie testowe, automatyczne pojawienie się wywołania Director, JSON i `valid: true` |
| Docelowy Compose 8080 | Kontenery healthy, `/health` HTTP 200; Buddy nadal meta, Director mock, jego zgoda płatna false. Ponownie ukończono oba questy klawiaturą; tym razem nośnik po prawej, potwierdzone drugie ukończenie |
| `git diff --check` | Bez błędów; wyłącznie informacyjne ostrzeżenia Git o CRLF/LF |

Pierwszy przebieg nowych testów wykrył, że Pydantic normalizował `true` do literału `1`; dodano walidator przed konwersją i ponowiono testy. Nie wykonano nowego płatnego wywołania Buddy’ego ani Directora. Test rozmowy w przeglądarce odbył się na osobnym backendzie mock ze sztucznym kluczem.

Dowody: [aktywny quest](evidence/quest-active.png), [ukończony quest](evidence/quest-completed.png), [JSON w Inspector](evidence/inspector-director.png), [wynik walidacji](evidence/inspector-validation.png), [rozmowa mock](evidence/buddy-regression.png). Materiały zawierają wyłącznie syntetyczne sesje testowe. Końcowa instancja 8080: [aktywny quest po prawej](evidence/localhost8080-active.png) i [ukończenie](evidence/localhost8080-completed.png). Izolowane kontenery 8081 po weryfikacji wyłączono; Compose na 8080 pozostaje uruchomiony.

## Uruchomienie i demonstracja

PowerShell, z katalogu repozytorium:

```powershell
cd C:\Users\piotr\projects\hakaton_meta\chess-corp-poc-codex
docker compose up --build -d
```

WSL:

```bash
cd /mnt/c/Users/piotr/projects/hakaton_meta/chess-corp-poc-codex
docker compose up --build -d
```

1. Otwórz http://localhost:8080 w nowej karcie lub odśwież Ctrl+Shift+R, poczekaj na runtime i kliknij Graj.
2. D do Buddy’ego, E i E/Enter do końca dialogu; Esc zamyka panel rozmowy.
3. A do turkusowego terminala przy lewym wejściu, E odbiera identyfikator; zakończ dialog.
4. D do Buddy’ego, E zalicza pierwszy quest; zakończ dialog i zamknij rozmowę Esc.
5. Poczekaj na drugi cel. Idź w stronę wskazaną przez silnik do turkusowo-złotego nośnika. Podejdź i naciśnij E. HUD pokazuje drugie ukończenie.
6. G poza rozmową ponawia wyłącznie nieudaną generację. R rozpoczyna nową grę i nową sesję. Po sukcesie nie ma ponownej generacji w tej samej sesji.
7. Otwórz http://localhost:8080/admin i zaloguj istniejącym ADMIN_TOKEN z `.env`. Widać osobno tryby Buddy i Director. Dla jury utwórz sesję demo i użyj jej linku gry oraz tokenu w `/admin/jury` w oddzielnym profilu — tak jak w dotychczasowej instrukcji `docs/AI_INSPECTOR.md`.

Domyślne ustawienia Directora, niezależne od Buddy’ego:

```dotenv
DIRECTOR_MODE=mock
DIRECTOR_ALLOW_PAID_REQUESTS=false
```

Aktualna lokalna konfiguracja Buddy’ego i jego sekretów została zachowana. `.env` nie jest częścią zmian Git. Nie trzeba zmieniać istniejącego MODEL_API_KEY, aby grać w scenariusz mock.

Do gry desktopowej: uruchom Compose jako backend, następnie `uv sync --locked` i `uv run python main.py`. Domyślny URL backendu to http://127.0.0.1:8080; można ustawić CHESS_CORP_API_URL. Bez backendu pierwszy quest nadal działa, a Director pokaże błąd połączenia i opcję G. Sam statyczny serwer pygbag nie zastępuje FastAPI.

## Prawdziwy Muse Spark — przygotowane, niewywołane

Dopiero po osobnej zgodzie na koszty ustawienie `DIRECTOR_MODE=meta` i `DIRECTOR_ALLOW_PAID_REQUESTS=true`, razem z istniejącymi MODEL_API_KEY i META_ALLOW_PAID_REQUESTS=true, pozwoli generować questy przez Meta. Po zmianie konfiguracji trzeba odtworzyć backend (`docker compose up -d --force-recreate backend`) i rozpocząć nową sesję R. Sam wybór modelu nie omija blokady kosztów. Tryb mock nie wykonuje HTTP do Meta nawet przy istniejącym prawdziwym kluczu.

Kontrakt oparto na oficjalnej dokumentacji [Meta Structured Outputs](https://dev.meta.ai/docs/structured-output) i [Chat Completions](https://dev.meta.ai/docs/protocols/chat-completions). Obsługa formatu została sprawdzona lokalnie na sztucznym HTTP; odpowiedź żywego API i jakość treści pozostają do sprawdzenia po zgodzie.

## Ograniczenia

- Jeden scenariusz po pierwszym dniu, jeden obiekt, dwie zatwierdzone lokalizacje. AI wybiera teksty i miejsce w ramach tego kontraktu, nie projektuje dowolnych mechanik ani scen.
- Stan klienta jest lokalnym stanem POC; kontekst API nie jest zabezpieczeniem antycheat. Nie ma trwałego zapisu, ekonomii ani autorytatywnego serwera rozgrywki.
- Cache planu i historii jest RAM, podlega istniejącym limitom sesji/TTL i znika po restarcie. Inspector również znika po restarcie, maksymalnie 200 wpisów. To nie jest trwała gwarancja jednokrotnej płatności po restarcie/wygaśnięciu sesji.
- Walidacja strukturalna i mechaniczna nie ocenia jakości opowieści. Stała wskazówka silnika pozwala znaleźć prawdziwy obiekt również przy nieprecyzyjnym tekście modelu.
- Bez Guarda, spacerowania NPC, audio i nowych grafik z API. Brak nowego ręcznego testu w oknie Chrome użytkownika; użyto przeglądarki wbudowanej. Pierwszy start interpretera WASM nadal wymaga Internetu.

## Następny najmniejszy krok

Po zgodzie na koszt wykonać jedną rzeczywistą generację Directora przez Muse Spark, obejrzeć JSON/walidację w Inspector i ukończyć otrzymany quest. Nie wymaga to zmiany mechaniki ani schematu.
