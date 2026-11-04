# Chess Corp — Living AI World

A playable cyberpunk game built with **Pygame CE / pygbag**, **FastAPI** and **Meta Muse Spark**. Explore four connected locations, talk to NPCs with individual identities, complete validated AI-generated quests, fight cyber-rats and buy equipment from Nyx. The AI Inspector exposes model decisions, token usage, validation and execution telemetry.

- **EN / PL:** English by default; click the language selector or press F2.
- **Living World:** shared, structured plans for multiple NPCs, short-term memory and deterministic local execution.
- **Quest Director:** COLLECT, SEQUENCE and LOGIC_PUZZLE, plus two fresh collection jobs per session. Rat bounty contracts are authored gameplay, not dynamically generated quests.
- **Safe demo:** mock mode works without an API key; real Meta calls require explicit environment flags and bounded budgets.
- **Inspector:** owner access at `/admin`; separate, expiring session-scoped jury access at `/admin/jury`.

## Quick start

```powershell
Copy-Item .env.example .env
# Set a long, random ADMIN_TOKEN in .env to enable the owner Inspector.
docker compose up --build -d
```

Open **http://localhost:8080/**. Defaults are MOCK with paid calls disabled. Never commit your `.env`, API key or spending ledgers. Real Meta configuration is described in the reports below; the repository does not include the local paid recording configuration.

Controls: **WASD** move, **E** interact, **T** NPC text chat, **F** doors, **J** session jobs, **Space** attack, **H** heal, **Tab** map, **M** audio, **F2** language, **R** new run.

The original artwork is supplied by the project owner and is not declared open source by this repository. Generated asset provenance is recorded in public manifests. Original synthesized audio has its own license in `assets/audio/LICENSE.md`.

## Development history and Polish documentation

The sections below document successive milestones. Statements about active modes, budgets and test counts are historical; current defaults are defined by `.env.example` and `backend/settings.py`.

# Chess Corp — grywalny POC

## Finał: połączony świat (04.11.2026)

Działają cztery lokacje: **ulica, oryginalny bar Cybroschligger, kryjówka hakerów i lobby**, z 10 NPC łącznie. **F** przy opisanych drzwiach przenosi do lokacji, **E** rozmawia/obsługuje obiekt, **Tab** pokazuje mapę. Questy, ekwipunek, rozmowy i NPC zachowują stan podczas podróży.

Uruchom `docker compose up --build -d`, otwórz nową kartę http://localhost:8080 i kliknij Graj. Drugie okno: http://localhost:8080/admin; dla jury użyj wydzielonej sesji i /admin/jury.

Obecnie **Buddy, Quest Director, World AI i Asset Generator są w mocku, wszystkie płatne zgody false**. Kryjówka zawiera już prawdziwą grafikę Muse Image z cache; nie generuje się przy starcie. Ukończony test: 3 World AI + 1 obraz, 0 płatnych Buddy i Quest Director. Ponowne włączenie World META opisuje raport; budżet domyślny to 3 wywołania na cały backend. Nie trzeba ponawiać obrazu.

[Pełny raport finału, testy, koszty i screenshoty](docs/changes/014-connected-living-world/REPORT.md).


NPC zatrzymuje się po podejściu, E wyświetla kolejną kwestię; po odejściu wraca do swoich zajęć. [Raport rozmów z NPC](docs/changes/013-npc-stop-and-talk/REPORT.md).

Bieżąca konfiguracja: **Buddy, Game Director i World AI wyłącznie MOCK; wszystkie zgody na płatne wywołania są wyłączone.** Uproszczony interfejs: jeden dialog, polskie czynności NPC i odsłonięta ulica. [Raport zmiany UI](docs/changes/012-readable-ui/REPORT.md).

## Living AI World — demo dla jury (04.11.2026)

Na ulicy działają czterej animowani NPC: Buddy, Security, Hacker i Employee. Każdy ma cel, nastrój i krótką pamięć. Świat działa od razu lokalnie; nie trzeba ukończyć pierwszego questu. Domyślnie World AI jest w trybie **MOCK**. Lokalne zachowania zastępcze są jawnie oznaczone **FALLBACK**.

Uruchom `docker compose up --build -d`, otwórz http://localhost:8080 i kliknij **Graj**. WASD — ruch, E — interakcja, Esc — zamknięcie rozmowy, R — nowy start. W drugim oknie otwórz http://localhost:8080/admin. Panel właściciela wymaga istniejącego `ADMIN_TOKEN`; do prezentacji utwórz tam sesję demonstracyjną i użyj jej linku gry oraz osobnego widoku `/admin/jury` z tokenem jury, najlepiej w oknie incognito.

Aby włączyć prawdziwe decyzje świata, w lokalnym `.env` ustaw:

```dotenv
WORLD_AI_MODE=meta
WORLD_AI_ALLOW_PAID_REQUESTS=true
WORLD_AI_SESSION_LIMIT=3
WORLD_AI_GLOBAL_LIMIT=3
WORLD_AI_MIN_INTERVAL_SECONDS=30
WORLD_AI_MAX_OUTPUT_TOKENS=1800
WORLD_AI_TOKEN_BUDGET=50000
```

Zachowaj istniejący `MODEL_API_KEY` na backendzie i `META_MODEL=muse-spark-1.3`. Po zmianie wykonaj `docker compose up -d --force-recreate backend game` i otwórz nową kartę gry. World AI ma własną zgodę na płatne wywołania; nie wymaga włączania Buddy’ego lub Game Directora. Jeżeli chcesz płacić wyłącznie za świat, ustaw dodatkowo `BUDDY_MODE=mock`, `DIRECTOR_MODE=mock`, `META_ALLOW_PAID_REQUESTS=false` i `DIRECTOR_ALLOW_PAID_REQUESTS=false`.

Planowanie następuje co około 31 sekund, z ostatnimi zdarzeniami i pamięcią NPC. Po trzech płatnych próbach cały backend przestaje generować następne plany i świat kontynuuje lokalnie. Limit globalny dotyczy jednego procesu backendu, wspólnie dla wszystkich okien; licznik RAM zeruje się po jego restarcie. W Compose działa jeden proces. Tokeny bez danych usage pozostają konserwatywnie zarezerwowane. Po pokazie ustaw `WORLD_AI_ALLOW_PAID_REQUESTS=false`, `WORLD_AI_MODE=mock` i odtwórz kontenery tą samą komendą.

W tym etapie wykonano **3 płatne wywołania World AI, 0 Buddy i 0 Game Director**. Wszystkie trzy plany przeszły walidację. Szczegóły, ograniczenia i dowody: [raport Living AI World](docs/changes/011-living-ai-world/REPORT.md).


[Dokumentacja projektu i raporty zmian](docs/README.md).

> **POC 04 — NPC Guard:** Buddy ma lokalną ochronę wejścia, kontekstu, historii i odpowiedzi. Inspector pokazuje **ALLOWED / OUT_OF_SCOPE / BLOCKED** oraz powód decyzji i odpowiedź dostarczoną graczowi. Jawne ataki i rozpoznane prośby spoza gry otrzymują odpowiedź lokalną, bez wywołania modelu; dozwolona rozmowa korzysta z dotychczasowego pojedynczego wywołania. [Raport POC 04](docs/changes/010-npc-guard/REPORT.md).

Guard działa w mocku i Meta bez dodatkowej usługi. Nie zmienia zasad questów. To ochrona warstwowa oparta na regułach i instrukcji postaci, nie gwarancja rozpoznania każdego możliwego jailbreaku. Instrukcja bezkosztowych testów znajduje się w raporcie.


> **POC 03.5 — Dynamic Quests & Puzzles:** Director obsługuje **COLLECT**, **SEQUENCE** i **LOGIC_PUZZLE**. W trybie mock naciśnij **F4 przed ukończeniem pierwszego questu**, aby wybrać scenariusz. Zagadkę otwiera **E**, cyfry wpisują odpowiedź, **Enter** sprawdza, **Esc** zamyka. Błędna kolejność terminali zeruje sekwencję. [Raport i wyniki POC 03.5](docs/changes/008-dynamic-quests-puzzles/REPORT.md).

Aktualizacja: `docker compose up --build -d`, potem zamknij starą kartę i otwórz [grę](http://localhost:8080/) w nowej. Inspector `/admin` pokazuje typ questu, plan, walidację i wynik wykonania. Nowe plany mają wersję 2; plany wersji 1 nadal działają jako COLLECT. Director pozostaje domyślnie mock, z `DIRECTOR_ALLOW_PAID_REQUESTS=false`.


> **POC 03 — AI Game Director:** po ukończeniu pierwszego questu automatycznie powstaje zadanie zebrania nośnika danych. Podejdź do wskazanego obiektu i naciśnij **E**. **Esc** zamyka rozmowę, **G** ponawia nieudaną generację, **R** rozpoczyna nową sesję. Director domyślnie działa jako **mock**, także gdy Buddy korzysta z Meta. [Raport POC 03 i instrukcja konfiguracji](docs/changes/006-ai-game-director/REPORT.md).

Historyczna weryfikacja POC 03: **75 testów**, Pygame **12 klatek**, pełne przejście obu questów w przeglądarce przez Docker Compose. Wyniki dalszych sekcji dotyczą historycznie POC 01. Do rozmów i Directora potrzebny jest uruchomiony backend; najprościej użyć `docker compose up --build -d`. Szczegóły aktualnych testów i ograniczeń są w raporcie POC 03.


> **AI Inspector:** [panel właściciela](http://localhost:8080/admin) i [widok jury](http://localhost:8080/admin/jury). Logowanie właściciela: `ADMIN_TOKEN` z lokalnego `.env`. [Instrukcja prezentacji i zabezpieczeń](docs/AI_INSPECTOR.md).

> **POC 02 jest zaimplementowany.** Uruchomienie: `docker compose up --build -d`, gra: http://localhost:8080. Domyślnie działa mock bez wywołań Meta. Podejdź do Buddy'ego, E, przewiń dialog zadania E/Enter; potem wpisuj wiadomość i wysyłaj Enter. Esc zamyka rozmowę. [Szczegółowy raport POC 02](docs/POC02_REPORT.md).

Jedna neonowa ulica z oryginalnych grafik, ruch WASD po ograniczonym pasie chodnika, cztery klatki animacji, Buddy, dialogi i zadanie: rozmowa → identyfikator przy wejściu po lewej → powrót. Dane sceny, dialogów i questu w `content/*.json`. POC 02 dodaje backend rozmów FastAPI; domyślny tryb mock nie korzysta z płatnych usług. Oryginały `grafika/` nie były zmieniane.

## Uruchomienie lokalne (PowerShell)

Wymagane: Python 3.12+ i uv. Sprawdzone: Python 3.13.3, uv 0.8.22, pygame-ce 2.5.8.

```powershell
cd C:\Users\piotr\projects\hakaton_meta\chess-corp-poc-codex
uv sync --locked
uv run python main.py
```

Po pierwszej instalacji gra działa lokalnie bez Internetu. Bez uv można użyć istniejącego środowiska: `.venv\Scripts\python.exe main.py`.

- A/D: lewo/prawo; W/S: głębia chodnika.
- E przy Buddy'm: rozmowa. E/Enter: następna wypowiedź; Esc: zamknięcie dialogu.
- Po rozmowie idź w lewo do turkusowego terminala „CHESS CORP”, wciśnij E, potem wróć do Buddy'ego i ponownie E.
- R poza dialogiem: nowa rozgrywka. Zamknięcie okna kończy grę.

Postęp aktualizuje się po rozpoczęciu właściwej interakcji. Zamknięcie dialogu Esc nie cofa odebranego przedmiotu. Ruch jest wstrzymany podczas dialogu. W scenie nie ma dodatkowych przeszkód wewnątrz pasa ruchu; granice chodnika blokują wejście w budynki i ulicę.

## Testy

```powershell
uv run python -m pytest -q
$env:SDL_VIDEODRIVER = 'dummy'
$env:SDL_AUDIODRIVER = 'dummy'
uv run python main.py --smoke
Remove-Item Env:SDL_VIDEODRIVER
Remove-Item Env:SDL_AUDIODRIVER
uv run python main.py --smoke
```

Wynik: **6 passed**. Pokryte: referencje JSON, kolejność etapów, brak przedwczesnego odbioru, brak podwójnej nagrody, promień i priorytet interakcji, ruch delta time, granice, blokady oraz przejście całego questu przez handler klawiszy z renderowaniem dialogów i restartem. Smoke test dummy: **12 klatek**. Start z rzeczywistym oknem SDL Windows: **12 klatek**, kod wyjścia 0. Zrzut: `docs/smoke.png`; został obejrzany podczas weryfikacji. Test integracyjny ustawia pozycje gracza, więc nie zastępuje pełnego ręcznego przejścia WASD.

## Przeglądarka — pygbag

```powershell
uv run python tools/build_web.py
uv run python -m http.server 8000 --bind 127.0.0.1 --directory web_app/build/web
```

Otwórz http://127.0.0.1:8000, poczekaj na pobranie runtime i kliknij obszar gry, aby nadać mu fokus. Serwer zatrzymasz Ctrl+C. Alternatywny serwer deweloperski: `uv run python -m pygbag web_app` (adres poda konsola). Nie otwieraj HTML przez `file://`.

Budowa z pygbag 0.9.3 zakończyła się kodem 0; wynik: `web_app/build/web/index.html` i `web_app.apk`. Skrypt pakuje wyłącznie pliki gry, JSON i pochodne grafiki; nie dodaje oryginałów ani środowiska uv. Po każdej zmianie kodu ponów pakowanie i budowę. Pętla `async def main()` oddaje sterowanie przez `await asyncio.sleep(0)` w każdej klatce, a zasoby są lokalizowane względem plików projektu. Wersja przeglądarkowa pobiera runtime z CDN pygame-web, dlatego pierwszy start wymaga Internetu.

## Zasoby i ograniczenia

Pełna inwentaryzacja 476 plików, parametry alfa i sposób cięcia: `docs/ASSET_REPORT.md`. Podgląd oryginałów: `docs/contact_sheet.png`. Wybrane grafiki pochodne są już dołączone, nie trzeba uruchamiać Pillow, by grać.

POC ma stały obszar renderowania 960×540, sterowanie klawiaturą, jedną scenę i jeden quest. Brak zapisu postępu, audio i sterowania dotykowego. Nie wprowadzono AI, walki ani innych mechanik.

### Wynik testu w przeglądarce

27.10.2026 uruchomiono zbudowany HTML w przeglądarce wbudowanej Codex. Po pobraniu runtime i kliknięciu ekranu wykonano pełną ścieżkę klawiaturą: D do Buddy'ego, E i Enter, A do terminala, E i Enter, D do Buddy'ego, E i Enter. HUD potwierdził odebranie identyfikatora, trzy zaliczone etapy i komunikat „ZADANIE UKOŃCZONE”. Dowód: `docs/web_completed.png`. Komunikaty runtime „MEDIA USER ACTION REQUIRED” przed pierwszym kliknięciem oznaczały oczekiwanie na gest użytkownika; po kliknięciu gra ruszyła.

Zauważone ograniczenie: domyślny szablon pygbag rozciąga canvas do rozmiaru dostępnego obszaru; w wąskim panelu proporcje są zniekształcone. Lokalny ekran 960×540 zachowuje proporcje. Następny najmniejszy krok: dopracować responsywne proporcje canvas w szablonie HTML i sprawdzić drugi rozmiar okna.

## Docker Compose — najprostszy start w przeglądarce

Wymagany działający Docker z Compose (na Windows: Docker Desktop w trybie kontenerów Linux; w WSL: integracja Docker Desktop z daną dystrybucją). Python ani uv na hoście nie są potrzebne. Polecenia wykonuj w katalogu zawierającym `compose.yaml`.

PowerShell:

```powershell
cd C:\Users\piotr\projects\hakaton_meta\chess-corp-poc-codex
docker compose up --build -d
```

WSL:

```bash
cd /mnt/c/Users/piotr/projects/hakaton_meta/chess-corp-poc-codex
docker compose up --build -d
```

Otwórz **http://localhost:8080**, poczekaj na runtime i kliknij ekran gry. Sterowanie: WASD, E, Enter, Esc, R. Pierwsza budowa pobiera obrazy i pygbag, a przeglądarka pobiera runtime z CDN — wymagany Internet. Gra wykonuje się w przeglądarce; kontener Nginx dostarcza pliki statyczne.

```bash
docker compose ps
docker compose logs --tail=50 game
docker compose down
```

Po zmianach w kodzie wykonaj ponownie `docker compose up --build -d` i odśwież stronę. Budowa samodzielnie przygotowuje paczkę pygbag z bieżących źródeł; nie wymaga istniejącego `web_app/`, `.venv` ani oryginalnego `grafika/`. `.dockerignore` ogranicza kontekst do plików gry i przetworzonych zasobów. Port jest dostępny tylko na komputerze lokalnym.

Jeżeli port 8080 jest zajęty, w WSL użyj `CHESS_CORP_PORT=8081 docker compose up --build -d`; w PowerShell najpierw `$env:CHESS_CORP_PORT='8081'`, potem `docker compose up --build -d`. Otwórz wtedy http://localhost:8081.

Konfiguracja budowy opiera się na [oficjalnej specyfikacji Compose](https://docs.docker.com/reference/compose-file/build/).

Weryfikacja Docker (28.10.2026): `docker compose config --quiet` bez błędów; `docker compose up --build -d` zakończone powodzeniem. Budowa użyła Linux/Python 3.12 i pygbag 0.9.3. GET `/` i `/web_app.apk` zwracają HTTP 200. Kontekst budowy miał około 160 kB. Ostrzeżenia pygbag o braku opcjonalnych Black i ffmpeg nie przerwały budowy (gra nie zawiera audio ani wideo).

Kontener osiągnął status `healthy`. W przeglądarce potwierdzono wyrenderowanie sceny, ruch D i rozmowę E z Buddy'm wraz ze zmianą celu. Zrzut: `docs/docker_running.png`. Kontener pozostawiono uruchomiony pod http://localhost:8080.

## Naprawa szarego ekranu pod localhost (28.10.2026)

Odtworzono błąd pod `http://localhost:8080/`: pygbag 0.9.3 wybierał deweloperski adres pakietów `http://localhost:8000/cdn/`, a pobranie Pygame kończyło się `Failed to fetch`. Wcześniejszy test pod `127.0.0.1` nie obejmował tego zachowania.

`tools/build_web.py` dołącza teraz przeglądarkowy pakiet pygame-ce 2.5.7 (CPython 3.12 / WebAssembly) do katalogu `runtime/`, sprawdza jego SHA256 i ustawia loader na bieżący origin kontenera. Wersja desktopowa nadal używa zależności z uv.lock. Ekran startu ma przycisk „Graj”, polskie komunikaty, obsługę błędów i możliwość ponowienia. Znika dopiero po pierwszej wyrenderowanej klatce. HTML ma nagłówek Cache-Control: no-store.

Sprawdzenie: 8 testów pytest przeszło; w przeglądarce na dokładnym adresie `http://localhost:8080/` kliknięto Graj i ukończono cały quest klawiaturą. Pobranie `/runtime/cp312/pygame_ce-2.5.7-cp312-cp312-wasm32_bi_emscripten.whl` zwróciło HTTP 200; nie było próby pobrania Pygame z portu 8000. Dowód: `docs/localhost_fixed.png`. Nie przeprowadzono osobnego testu w oknie Chrome użytkownika — dostęp do niego zakończył się limitem czasu.

Po aktualizacji: `docker compose up --build -d`, następnie zamknij starą kartę gry i otwórz nową pod http://localhost:8080. Jeśli nadal widzisz starą wersję, użyj Ctrl+Shift+R. Internet jest nadal potrzebny do pobrania interpretera Python/WASM z CDN.


## Finał 015 — cyber-szczury, kontrakty Barmana i Nyx

Gra: http://localhost:8080. Uruchom w katalogu projektu: `docker compose up --build -d`.
Otwórz świeżą kartę (stara karta zachowuje poprzedni kod WASM).

1. Wejdź do BARU prawymi drzwiami ulicy: WASD i **F**.
2. Podejdź do **Barmana** i naciśnij **E**, aby przyjąć deratyzację. NPC zatrzyma się przy graczu.
3. Wróć na ulicę przez lewe drzwi baru (**F**). **Spacja**: cios pałką, można przytrzymać; **H**: apteczka. Walcz blisko szczura, patrząc w jego stronę.
4. Pokonaj 3 szczury. Łup: 2 KR za każdego. Wróć do Barmana i **E**: wypłata 30 KR. Razem 36 KR.
5. W barze po prawej znajdziesz **Nyx**. **E** otwiera sklep; góra/dół wybiera, Enter/E kupuje, Esc zamyka. Apteczka 8 KR, pałka +1 za 18 KR, pancerz za 22 KR.
6. Kolejne **E** u Barmana rozpoczyna trudniejszy kontrakt: 5 szczurów, 3 KR łupu/szt. i 60 KR nagrody. Po śmierci Enter przywraca gracza za maksymalnie 5 KR; zabite szczury i questy pozostają zaliczone.
7. Pierwszy quest, Buddy, Guard, questy Director COLLECT/SEQUENCE/LOGIC_PUZZLE, mapa i wszystkie cztery lokacje działają niezależnie. Zmiana lokacji zachowuje ekwipunek, HP, kredyty i zakupy. R/odświeżenie zaczyna nową grę.

Szczur i Nyx są rzeczywistymi assetami `muse-image-1.0` zapisanymi w cache. Ich cztery klatki to lokalna animacja pochodna; kolejne szczury nie generują kosztów. Dawne grafiki, bar i poster Meta w kryjówce pozostają dostępne.

W lokalnym `.env` finał ma **World AI META**, osobną zgodę i limity: 6 planów/sesję, 12 płatnych prób łącznie dla etapu 015, minimum 30 sekund, do 2400 tokenów odpowiedzi, budżet 150000 tokenów. Trwały licznik `assets/generated/.world-ai-stage-015.json` obejmuje trzy już wykonane próby LIVE. Nie usuwaj go, aby restart nie odnawiał budżetu. Po wyczerpaniu limitu działa jawny FALLBACK. Buddy i Quest Director pozostają mock; generowanie kolejnych obrazów jest wyłączone, gotowy cache działa nadal.

Aby wyłączyć koszty: w `.env` ustaw `WORLD_AI_MODE=mock` i `WORLD_AI_ALLOW_PAID_REQUESTS=false`, następnie `docker compose up -d --force-recreate backend game`. `.env.example` celowo ma bezpieczne domyślne mock/false. Pliki `.env`, prywatne metadane generacji i liczniki nie trafiają do Git ani paczki WWW.

Inspector: http://localhost:8080/admin. World pokazuje kontekst walki/kontraktów, NPC, plany i wykonanie. Asset Generator pokazuje szczura i Nyx, model, źródło, czas i podgląd. Wczytanie cache nie jest nowym wywołaniem Meta. Dla jury korzystaj z osobnego, wygasającego widoku `/admin/jury` i sesji utworzonej w panelu właściciela.

Testy: `uv run pytest -q`. Dodatkowe scenariusze klawiaturowe w `tools/browser015.py` i `tools/browser015_final_mock.py` wymagają testowego Playwright + Chrome i trzech integracji w mocku; sprawdzają tryby przed uruchomieniem. Skrypty `*live*015*` / `browser015_live*` dokumentują jednorazowy kontrolowany test; nie są instrukcją uruchamiania kolejnych płatnych prób.

Szczegółowy raport: [015 — kontrakty i Nyx](docs/changes/015-rat-bounties-and-merchant/REPORT.md).


## POC 016 — Cyberpunk Sound Design (zmiana 017)

Dźwięk uruchamia się po kliknięciu **Graj** lub pierwszej interakcji. **M** włącza/wyłącza audio; wyciszenie oznacza tylko mały napis przy dole ekranu. Podczas wpisywania tekstu Buddy’emu litera M pozostaje częścią wiadomości. Ustawienie wyciszenia utrzymuje się po R w tej samej karcie.

Cztery lokalne, zapętlone ambienty: deszcz/miasto na ulicy, przytłumiony klub w barze, serwery w kryjówce i wentylacja/elektronika w lobby. Jeden kanał ambientu zapobiega nakładaniu lokacji; przejścia mają krótki fade. Efekty obejmują rozmowę E, drzwi, sklep, zakup, wypłatę kontraktu, zamach/trafienie/pokonanie szczura i apteczkę. Brak urządzenia lub uszkodzony plik nie blokuje gry.

Wszystkie 14 plików WAV w `assets/audio/` powstały lokalnie z oscylatorów i szumu, bez nagrań osób trzecich i bez płatnego API. Pochodzenie, formaty i hashe: `assets/audio/manifest.json`. Audio i jego generator są dedykowane CC0-1.0; nie zmienia to licencji oryginalnych grafik. Odtwarzanie nie pobiera plików z sieci — pliki są w paczce gry. Ponowna synteza wyłącznie w fazie przygotowania: `uv run python tools/generate_audio.py`.

Start bez zmian: `docker compose up --build -d`, następnie świeża karta http://localhost:8080 i Graj. Pygbag pakuje krótkie, sprawdzone PCM WAV bez automatycznego konwertowania przez ffmpeg. Nie trzeba instalować nowych usług. Jeśli przeglądarka blokuje audio, kliknij płótno gry lub naciśnij klawisz; M sprawdza wyciszenie. To dotyczy polityki audio przeglądarki, nie dostępu do Meta.

Zgodnie z późniejszym poleceniem użytkownika lokalna konfiguracja Buddy, Quest Director i World AI jest teraz META. Testy audio w przeglądarce odbywają się z rzeczywistym World LLM; koszt dotyczy istniejącego planowania NPC, nigdy generacji audio. Liczników nie zerowano. Po późniejszym zatwierdzeniu limit World AI wynosi 6/sesję i 50 globalnie, bez resetowania wykorzystanych prób; po wykorzystaniu budżetu działa jawny FALLBACK, nie mock. Nie zmieniano mechaniki questów ani stanów gry.

Raport audio: [017 — POC 016 Sound Design](docs/changes/017-cyberpunk-sound-design/REPORT.md).


## Aktualne sterowanie — zmiana 018

**Spacja** atakuje stale także poza kontraktem. Trafiony NPC odpowiada walką; ważne postacie po ogłuszeniu wracają, aby nie blokować gry. Pałka od Nyx zwiększa obrażenia. **T przy NPC** otwiera jego osobny czat META z własną tożsamością i historią. **E** zachowuje akcje fabularne i sklep.

**J** pokazuje dwie nowe misje zbierackie generowane przez META na świeżą sesję, bez czekania na ukończenie pierwszego dnia. Zbieraj złote przedmioty E; nagroda 15–45 KR za zlecenie trafia do portfela automatycznie i tylko raz. R albo nowe uruchomienie tworzy nowe zapytanie do Directora. Dotychczasowe questy są zachowane.

W /admin jest wybór grafiki i przyciski **Wygeneruj nowy asset** oraz **Usuń zapisane pliki assetu**. Regeneracja jest jawna, płatna i nie powtarza tego samego żądania. Czyszczenie nie usuwa oryginałów ani liczników wydatków. Gra odbiera nowe wersje obrazów w ciągu około 10 s, bez przebudowy Dockera. Grafiki nie generują się automatycznie przy każdym starcie — zgodnie z wyborem użytkownika.

Uruchomienie nadal: `docker compose up --build -d`, http://localhost:8080 i świeża karta/Ctrl+F5. [Raport 018](docs/changes/018-npc-combat-chat-and-session-jobs/REPORT.md).

### Język EN / PL

Gra i widok `/admin/jury` domyślnie używają angielskiego. Kliknij **EN / PL** w nagłówku gry albo naciśnij **F2**. Wybór jest zachowany przy zmianie lokacji i odświeżeniu strony. Panel `/admin` domyślnie używa polskiego i ma własny przełącznik języka.

Nowe odpowiedzi NPC i plany AI otrzymują instrukcję wybranego języka. Starsze wyniki w innym języku pozostają oznaczonym oryginałem. Identyfikatory i surowe dane techniczne JSON pozostają bez zmian.

Raport: [lokalizacja EN/PL](docs/changes/019-en-pl-localization/REPORT.md).
