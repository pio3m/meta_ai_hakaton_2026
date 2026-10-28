# Chess Corp — grywalny POC

Jedna neonowa ulica z oryginalnych grafik, ruch WASD po ograniczonym pasie chodnika, cztery klatki animacji, Buddy, dialogi i zadanie: rozmowa → identyfikator przy wejściu po lewej → powrót. Dane sceny, dialogów i questu w `content/*.json`. Brak płatnych usług i backendu. Oryginały `grafika/` nie były zmieniane.

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
