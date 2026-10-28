# POC 02 — Buddy: API, rozmowa i pamięć sesji

## Uruchomienie (domyślnie mock, bez opłat)

```bash
docker compose up --build -d
docker compose ps
```

Otwórz http://localhost:8080, kliknij Graj. Jeśli masz otwartą starą wersję, zamknij kartę i otwórz nową albo użyj Ctrl+Shift+R. Port gry pozostaje 8080. FastAPI jest dostępne przez ten sam Nginx, bez osobnego portu hosta:

- `GET http://localhost:8080/health`
- `POST http://localhost:8080/api/chat`

Zatrzymanie: `docker compose down`. Logi: `docker compose logs --tail=50 backend`.

Domyślna konfiguracja to `BUDDY_MODE=mock` i `META_ALLOW_PAID_REQUESTS=false`. Nie musisz tworzyć `.env`, aby korzystać z mocka. Przykład ustawień jest w `.env.example`; `.env` jest ignorowany przez Git i wykluczony z kontekstu budowy obrazów. Nie wpisuj klucza do gry ani plików JavaScript.

W PowerShell katalog projektu:

```powershell
cd C:\Users\piotr\projects\hakaton_meta\chess-corp-poc-codex
```

W WSL:

```bash
cd /mnt/c/Users/piotr/projects/hakaton_meta/chess-corp-poc-codex
```

## Rozmowa i zachowanie questu

1. Podejdź do Buddy'ego i naciśnij E. Działają dotychczasowe dwie wypowiedzi zadania — przewiń je E lub Enter.
2. Po ostatniej wypowiedzi pojawia się pole swobodnej rozmowy. Wpisuj tekst; Enter wysyła wiadomość, Esc zamyka okno.
3. W trakcie oczekiwania widzisz „Buddy pisze...”. Esc pozwala od razu wrócić do gry, a odpowiedź zostanie zachowana w historii po zakończeniu żądania.
4. Rozmowę można ponownie otworzyć przy Buddy'm także podczas etapu odbioru identyfikatora. Historia nie znika po zamknięciu okna.
5. Zadanie nadal wymaga osobistej interakcji z terminalem po lewej, a następnie powrotu do Buddy'ego. Tekst odpowiedzi AI nie jest wykonywany i nie przyznaje przedmiotów.

Sterowanie czatem: Backspace/Delete, strzałki, Home/End; PgUp/PgDn lub kółko myszy przewijają historię. F2 zmienia język odpowiedzi PL/EN. F3 po błędzie przywraca ostatnią wiadomość do edycji i ponownego wysłania. Limit wiadomości: 600 znaków. R działa po zamknięciu dialogu i rozpoczyna nową grę oraz nową sesję rozmowy.

Mock jawnie oznacza odpowiedzi jako `[MOCK — bez AI]`. To deterministyczny symulator połączenia, korzystający z kontekstu i poprzedniej wiadomości, a nie generowanie przez model. Dopiero tryb Meta generuje swobodne odpowiedzi.

## Implementacja

| Część | Pliki | Odpowiedzialność |
|---|---|---|
| API | `backend/app.py`, `models.py` | health, chat, walidacja, bezpieczne komunikaty błędów |
| Konfiguracja | `backend/settings.py` | środowisko, timeout, klucz jako SecretStr, jawna blokada płatnych wywołań |
| Dostawcy | `backend/providers.py` | mock oraz asynchroniczny adapter HTTP Meta |
| Pamięć | `backend/history.py` | repozytorium wymienne przez Protocol, kolejność i limity sesji |
| Pygame | `game/chat.py`, `main.py`, `game/ui.py` | edycja tekstu, historia, oczekiwanie, responsywna pętla |
| Przeglądarka | `web/chat_bridge.js` | fetch i AbortController; ten sam origin, bez klucza API |
| Uruchamianie | `compose.yaml`, `backend/Dockerfile`, `nginx.conf` | dwa kontenery, reverse proxy, healthchecki |

Backend otrzymuje tylko sesję, NPC, wiadomość, język i mały kontekst: `quest_id`, `quest_status`, `has_badge`. Kontekst służy do dialogu, nie do autoryzacji. Odpowiedź zawiera tekst i ograniczoną historię, nie komendy silnika gry.

Historia: domyślnie 10 par wiadomości, do 100 sesji, TTL 3600 sekund. Czyszczenie TTL następuje przy kolejnym żądaniu; pojemność jest ograniczona także bez upływu TTL. Żądania tej samej sesji są serializowane blokadą, a zajęte sesje nie są usuwane. Inne sesje nie czekają na tę blokadę. Nieudane żądanie nie dopisuje niepełnej pary do historii backendu.

Frontend zachowuje ostatnie 20 wiadomości. Sesja istnieje przez czas bieżącej rozgrywki; odświeżenie strony i R tworzą nowy identyfikator. Restart backendu usuwa historię pamięciową. Nie ma bazy danych ani pamięci długoterminowej.

Na desktopie HTTP wykonuje się w wątku przez `asyncio.to_thread`; w przeglądarce używany jest nieblokujący fetch. Odpowiedzi są odbierane przez zadanie asyncio, bez zatrzymywania renderowania. Polskie znaki przechodzą przez JSON z escapowaniem Unicode na granicy JS/Python, aby uniknąć błędnej konwersji UTF-8 w FFI pygbag.

## Integracja Meta — przygotowana, wyłączona

Dokumentację zweryfikowano 28.10.2026:

- [Meta Model API — overview](https://dev.meta.ai/docs/overview): bazowy adres `https://api.meta.ai/v1`, modele Muse Spark i Bearer token.
- [Chat Completions](https://dev.meta.ai/docs/protocols/chat-completions): `POST /v1/chat/completions`, role developer/user/assistant, odpowiedź w `choices[0].message.content`.
- [Muse Spark](https://dev.meta.ai/models/muse-spark): model `muse-spark-1.3`.

Adapter używa `httpx.AsyncClient`, modelu ze środowiska, `max_completion_tokens=1024` i `reasoning_effort=minimal`. Prompt ustala osobowość Buddy'ego, język i ogranicza go do dialogu. Do Meta trafia ograniczona historia i aktualny kontekst, bez narzędzi mogących zmieniać świat gry.

Dopiero po uzyskaniu zgody na koszt można skopiować `.env.example` do `.env` i ustawić:

```dotenv
BUDDY_MODE=meta
MODEL_API_KEY=twoj-klucz
META_MODEL=muse-spark-1.3
META_API_BASE_URL=https://api.meta.ai/v1
META_TIMEOUT_SECONDS=25
META_ALLOW_PAID_REQUESTS=true
```

Potem `docker compose up -d --build`. Brak klucza lub `META_ALLOW_PAID_REQUESTS=false` daje czytelne HTTP 503 bez wykonywania żądania Meta. Nie ma automatycznych powtórzeń płatnych żądań. Timeout daje 504, limit dostawcy 429, błędna odpowiedź lub pozostałe błędy dostawcy 502. Odpowiedzi nie ujawniają klucza ani surowych wyjątków. Health działa również przy nieaktywnej konfiguracji AI.

**Podczas implementacji nie wykonano żadnego rzeczywistego wywołania generowania Meta.** Adapter jest sprawdzany przez `httpx.MockTransport` i odpowiedzi testowe. Dostępność konkretnego konta i modelu oraz jakość prawdziwych odpowiedzi wymagają późniejszego testu po zgodzie.

## Testy i uruchomienie desktopowe

```bash
uv sync --locked
uv run python -m pytest -q
uv run python main.py --smoke
```

Grupy dev i backend instalują się domyślnie, więc dotychczasowa komenda testów nadal działa. W headless ustaw `SDL_VIDEODRIVER=dummy` i `SDL_AUDIODRIVER=dummy` przed smoke testem.

Opcjonalnie sam backend bez Dockera:

```bash
uv run uvicorn backend.app:app --host 127.0.0.1 --port 8001
```

W drugim terminalu ustaw `CHESS_CORP_API_URL=http://127.0.0.1:8001` i uruchom `uv run python main.py`. Zmienna środowiskowa jest odczytywana przez klienta desktopowego; wersja webowa zawsze korzysta z `/api/chat` na bieżącym origin.

## Zakres i ograniczenia

Nie zmieniono plików oryginalnych ani przetworzonych grafik, `game/player.py`, `game/world.py`, `game/quests.py`, sceny i definicji questu. Zachowano istniejące teksty etapów. Dodano tylko dodatkową wypowiedź Buddy'ego podczas oczekiwania na identyfikator i pole swobodnej rozmowy po dialogu zadania.

Backend pracuje w jednym procesie/workerze, co jest wymagane dla spójnej pamięci RAM. Nie jest to serwer publiczny z kontami graczy; identyfikator sesji nie jest mechanizmem autoryzacji. Nie ma streamingu tokenów, rozmowy głosowej ani zapisu na dysku. Ewentualna awaria API nie zmienia stanu questu; lokalne dialogi zadania działają bez odpowiedzi backendu.

Plik `tasks/02_BUDDY_AI.md` kończy się w połowie zdania w sekcji 12. Zrealizowano widoczne wymagania oraz wymaganie responsywności z wiadomości użytkownika.

Następny najmniejszy krok: po osobnej zgodzie i konfiguracji klucza wykonać jedną kontrolowaną rozmowę Meta i ocenić odpowiedź oraz czas oczekiwania.

## Wyniki weryfikacji wykonanej 28.10.2026

| Sprawdzenie | Wynik |
|---|---|
| Testy przed zmianami `uv run python -m pytest -q` | 8 passed |
| Testy po implementacji tą samą komendą | **38 passed** (7,43 s w ostatnim przebiegu) |
| Smoke test Pygame dummy | 12 wyrenderowanych klatek |
| Smoke test Pygame, rzeczywiste okno Windows | 12 wyrenderowanych klatek, exit 0 |
| `docker compose config --quiet` | poprawny Compose |
| `docker compose up --build -d` | oba obrazy zbudowane i kontenery uruchomione |
| `docker compose ps` | game i backend: healthy; host wyłącznie 8080 |
| `GET /health` przez Nginx | 200, status ok, mode mock |
| Rzeczywisty klient desktopowy → Compose | dwie wiadomości PL, poprawne Unicode, historia 2 → 4 wpisy |
| Pygame/pygbag → JS fetch → Nginx → FastAPI | rozmowa w przeglądarce, HTTP 200 |
| Polski tekst „Zażółć gęślą jaźń” | poprawny przed wysłaniem i w odpowiedzi |
| Zamknięcie i ponowne otwarcie rozmowy | historia zachowana; kolejna odpowiedź mock przywołuje poprzednie pytanie |
| F2, pytanie po angielsku | odpowiedź mock po angielsku |
| Wyłączenie kontenera backend | czytelny błąd w grze, Esc przywraca ruch |
| Pierwszy quest podczas awarii backendu | odebrano identyfikator, powrót do Buddy'ego, komunikat ZADANIE UKOŃCZONE |
| Kontekst po ukończeniu i przywróceniu backendu | Buddy odwołuje się do ukończonego zadania |
| Mocki wywołań Meta | kontrakt URL/auth/model/history oraz timeout/401/429/500, błędny JSON i pusta odpowiedź sprawdzone bez Internetu |
| Zgoda i klucz | brak zgody lub brak klucza nie wykonuje żądania HTTP Meta |
| Grafiki, ruch, automat questu, scena | `git diff --exit-code` potwierdza brak zmian |
| Dotychczasowe teksty dialogów | porównane z pierwszym commitem; identyczne |

Podczas budowy wystąpiło przerwane pobranie WASM z CDN. Naprawiono je przez weryfikowany SHA256 cache, ponawianie i limity czasu; kolejne zmiany kodu korzystają z osobnej warstwy cache Dockera. Podczas rzeczywistego testu przeglądarki wykryto też błędną konwersję Unicode na granicy JS/Python; po poprawce ponownie potwierdzono poprawne polskie znaki.

Pytest zgłasza jedno ostrzeżenie biblioteki Starlette: używanie httpx z TestClient jest oznaczone jako deprecated. Nie jest to błąd testu ani awaria API. Opcjonalne ostrzeżenia budowy pygbag o Black/ffmpeg nie blokują gry.

Zrzuty z rzeczywistych testów:

- `docs/poc02_chat.png`: polskie znaki i pamięć poprzedniej wiadomości.
- `docs/poc02_unavailable.png`: komunikat po wyłączeniu backendu.
- `docs/poc02_quest_complete.png`: ukończenie questu po dodaniu czatu, przy wyłączonym API.

Backend po teście awarii został przywrócony i pozostaje w trybie mock. Oba kontenery pozostawiono uruchomione. Zmiany POC 02 nie zostały automatycznie zacommitowane.
