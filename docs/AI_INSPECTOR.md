# AI Inspector — pokaz pracy Buddy’ego

## Dwa okna podczas prezentacji

1. Otwórz **http://localhost:8080/admin** i zaloguj się wartością `ADMIN_TOKEN` z lokalnego `.env`. Token właściciela został wygenerowany losowo; nie jest kluczem Meta.
2. Kliknij **Utwórz sesję demonstracyjną**. Panel pokaże link do gry i jednorazowo token jury.
3. W pierwszym oknie otwórz **link gry demonstracyjnej** z panelu. Tylko ta gra otrzyma identyfikator przypisany do podglądu jury.
4. W drugim oknie, w **osobnym profilu przeglądarki albo incognito**, otwórz **http://localhost:8080/admin/jury** i zaloguj się tokenem jury. Nie loguj tam właściciela i nie udostępniaj jury jego sesji przeglądarki.
5. Rozmawiaj z Buddy’m w grze. Panel odświeża się co sekundę; opcja **Śledź najnowsze** automatycznie wybiera nowy wpis. Wybranie starszego wywołania wyłącza śledzenie.

Panel sam nie wysyła żadnych zapytań do modelu. W działającym trybie Meta opłaty mogą powstawać dopiero po wysłaniu wiadomości w grze.

## Właściciel i jury

| Dane / czynność | Właściciel `/admin` | Jury `/admin/jury` |
|---|---|---|
| Ostatnie wywołania | Wszystkie zachowane sesje | Tylko jedna aktywna sesja demo |
| Wiadomość i odpowiedź | Tak | Tak, wyłącznie demo |
| Kontekst questu | Tak | Tak, wyłącznie demo |
| Pełny payload i historia w `messages` | Tak, po maskowaniu sekretów | Nigdy |
| Identyfikatory sesji | Tak | Ukryte |
| Czas, model, tokeny, błędy | Tak | Tak, wyłącznie demo |
| Tworzenie i cofanie dostępu jury | Tak | Nie |

Token jury jest ważny 30 minut i ograniczony po stronie serwera do dokładnie jednej sesji. Utworzenie nowej sesji demo unieważnia poprzedni dostęp jury. Przycisk **Cofnij dostęp jury** odcina odczyt również dla już otwartego panelu; dane są czyszczone przy następnym odświeżeniu. Parametr `session_id` w adresie API nie zmienia zakresu jury.

R w grze rozpoczyna nową zwykłą sesję i kończy powiązanie z bieżącym pokazem. Do kolejnej prezentacji utwórz nową sesję demo i otwórz jej nowy link gry.

## Co jest rejestrowane

Bufor w RAM przechowuje maksymalnie **200 wywołań**. Nowy wpis pojawia się w stanie `pending` przed oczekiwaniem na model, następnie zmienia się na `ok` lub `error`.

W Meta payload jest przechwytywany w miejscu faktycznego `httpx.AsyncClient.post`, a nie rekonstruowany później. Obejmuje dokładną tablicę wiadomości: instrukcję Buddy’ego, aktualny kontekst, historię oraz pytanie gracza, a także parametry żądania. Zapis obejmuje też odpowiedź, monotonicznie mierzony czas wykonania, model żądany i zwrócony przez API, status HTTP dostawcy oraz jego `usage` (`prompt_tokens`, `completion_tokens`, `total_tokens`), jeśli jest dostępne. Nie estymujemy brakujących tokenów.

Mock jest wyraźnie opisany jako symulacja: prompt nie został wysłany do modelu, tokeny mają wartość „brak danych”. Nieudana próba Meta z zablokowaną konfiguracją ma oznaczenie niewysłanego żądania. Surowe wyjątki i odpowiedzi błędów dostawcy nie trafiają do panelu; pokazywany jest bezpieczny komunikat i status.

Bardzo długa odpowiedź jest ograniczana w inspektorze do 16000 znaków i oznaczana jako ucięta. Cały bufor i dane logowania sesji są usuwane po restarcie backendu. Nie ma zapisu na dysku ani odtwarzania wywołań wykonanych przed wdrożeniem Inspectora. Pamięć pozostaje w jednym workerze FastAPI zgodnie z dotychczasową konfiguracją.

## Ochrona danych

- Bez skonfigurowanego `ADMIN_TOKEN` dostęp właściciela jest zamknięty.
- Właściciel i jury mają odrębne loginy, cookies i endpointy. Jury nie otrzymuje uprawnień właściciela.
- Cookies są HttpOnly i SameSite=Strict. Sesja właściciela wygasa po 8 godzinach; nie trzymamy tokenów w localStorage ani adresach URL. Tokeny sesji są przechowywane w RAM jako skróty.
- Dane panelu mają `Cache-Control: no-store`; dodano CSP, blokadę osadzania i kontrolę Origin dla operacji POST. Treści modelu są wyświetlane jako tekst, bez interpretowania HTML.
- Nie rejestrujemy nagłówków HTTP, klucza API ani cookies. Skonfigurowany klucz Meta i token właściciela, rozpoznane tokeny sesji oraz typowe wzorce sekretów są maskowane przed zapisaniem rekordu.
- Maskowanie nie rozpoznaje dowolnych danych osobowych lub sekretów zapisanych naturalnym językiem. W sesji przeznaczonej dla jury używaj wyłącznie treści prezentacyjnych.
- Pozostaje dotychczasowy dostęp lokalny na `127.0.0.1:8080`; panel jest przeznaczony do lokalnej prezentacji, a nie publicznego hostingu.

## Uruchomienie i token właściciela

```bash
docker compose up --build -d
```

Lokalne `.env` jest ignorowane przez Git oraz wykluczone z obrazu Dockera. `ADMIN_TOKEN` nie jest wypisywany w dokumentacji ani dostarczany do Pygame. W `.env.example` znajduje się wyłącznie pusta zmienna. Aby zmienić token właściciela, wpisz nową losową wartość o długości co najmniej 32 znaków do `.env` i odtwórz backend przez `docker compose up -d`; dotychczasowe sesje oraz RAM zostaną wyczyszczone.

## Weryfikacja

- Testy bazowe przed zmianami: **38 passed**.
- Testy obejmują: brak dostępu bez logowania, cookie HttpOnly/SameSite, logout, brak cache, Origin/CSRF, limit 200 rekordów, redakcję sekretów, dokładny payload, model, tokeny, czas i błędy, widoczność wpisu pending, rozdzielenie równoległych wywołań, zakres jury, próby zmiany sesji przez query string, wygaśnięcie oraz cofnięcie dostępu.
- Kontrakt i `usage` prawdziwego adaptera Meta są testowane przez `httpx.MockTransport` — bez połączenia z Meta.
- Testy w przeglądarce wykonano w odrębnym Compose na porcie 8081, w trybie mock z fałszywym kluczem. Potwierdzono logowanie, aktualizację bez odświeżania, payload z historią i kontekstem, śledzenie najnowszego wpisu i ograniczony widok jury.
- Wywołanie wysłane z Pygame przez link gry demo pojawiło się w panelu. Syntetyczne wywołanie innej sesji było widoczne dla właściciela, ale nie dla jury. Po wylogowaniu właściciela jury nadal widziało tylko dozwoloną sesję.
- Zrzuty: `docs/inspector_owner.png` i `docs/inspector_jury.png`. Wszystkie przedstawiają tryb mock.
- Nie wykonano dodatkowych płatnych wywołań Meta. W działającym środowisku zapis pierwszego rzeczywistego wywołania nastąpi dopiero, gdy użytkownik wyśle kolejną wiadomość.

Kod: `backend/inspector.py`, `backend/admin_routes.py`, `backend/admin/`. Nie dodano Langfuse, bazy ani dodatkowych usług.

Wynik końcowy: **50 passed** (`uv run python -m pytest -q`), jedno wcześniejsze ostrzeżenie deprecacyjne Starlette/TestClient. Oba kontenery właściwej gry mają status `healthy`, port pozostaje 8080, backend zachował tryb `meta`. Na właściwym porcie sprawdzono: odczyt bez logowania daje 401, logowanie lokalnym ADMIN_TOKEN działa, odczyt właściciela ma `no-store`, wylogowanie działa. Bufor po wdrożeniu jest pusty i nie zawiera syntetycznych rekordów testowych. Pomocnicze środowisko mock na 8081 zostało zatrzymane i usunięte. Podczas tego zadania nie wysłano żadnego dodatkowego żądania generowania do Meta.
