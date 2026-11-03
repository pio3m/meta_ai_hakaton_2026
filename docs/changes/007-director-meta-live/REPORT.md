# POC 03 — raport rzeczywistego AI Game Directora

Data: 2026-11-02 (Europe/Warsaw). Status: test zakończony powodzeniem; zgoda na kolejne płatne wywołania Directora wyłączona.

## Cel i zakres

Jedno kontrolowane wywołanie istniejącej integracji Meta Muse Spark, maksymalnie jedna płatna próba za zgodą użytkownika. Sprawdzenie poprawności JSON, walidacji, pojawienia się questa, ukończenia w przeglądarce oraz zapisu rzeczywistego wywołania w AI Inspector.

Wszystkie pięć sprawdzeń zakończyło się powodzeniem. Nie użyto mocka jako odpowiedzi tego testu ani nie zastąpiono odpowiedzi modelu ręcznie przygotowanym planem.

## Przygotowanie i ochrona kosztów

- Odczytano AGENTS.md, bieżący adapter, schemat, walidator, konfigurację Compose i zasady raportowania. Potwierdzono obecność klucza i tokenu administracyjnego bez wypisywania ich wartości.
- Konfiguracja przed testem: Buddy `meta`, model `muse-spark-1.3`, baza `https://api.meta.ai/v1`, wspólna istniejąca zgoda Meta włączona; Director `mock`, jego osobna zgoda `false`.
- Uruchomiono izolowany Compose `chess-director-live` na `127.0.0.1:8081`. Standardowa instancja 8080 pozostała bez zmian.
- Tymczasowy moduł startowy opakował istniejący adapter w blokadę jednej próby na cały proces, obejmującą wszystkie sesje i ponowienia. Zajęcie limitu następowało przed wywołaniem adaptera; w `finally` zamykano zgodę Directora i zgodę jego własnego adaptera HTTP. Nie zmieniano adaptera Buddy’ego.
- Blokada nie wykonywała generacji sama: jedynym wyzwalaczem było ukończenie pierwszego questu w przeglądarce. Nie wysyłano wiadomości do Buddy’ego, użyto wyłącznie istniejących dialogów pierwszego questu.
- W `.env` jawnie ustawiono `DIRECTOR_ALLOW_PAID_REQUESTS=false` jeszcze przed testem. Krótkie włączenie dotyczyło wyłącznie izolowanej konfiguracji testowej. Nie wykonywano automatycznego ponowienia.

## Wynik rzeczywistego wywołania

| Parametr | Wynik |
|---|---|
| Liczba prób Directora | **1** |
| Nowe wywołania Buddy’ego | **0** |
| Model odpowiedzi | `muse-spark-1.3` |
| Status HTTP Meta | **200** |
| Czas całego endpointu / walidacji w Inspector | **2930,4 ms** |
| Tokeny wejściowe | **649** |
| Tokeny wyjściowe | **434** |
| Tokeny razem | **1083** |
| Rzeczywisty payload HTTP | Inspector: `sent_to_model=true`, zawiera istniejący prompt, kontekst i `response_format=json_schema` |
| Odpowiedź | Poprawny obiekt JSON, bez kodu wykonywalnego i bez bloku Markdown |
| Walidacja backendu | `valid=true`, `errors=[]` |
| Zmiana schematu/promptu po odpowiedzi | Nie była potrzebna |

Czas jest pomiarem endpointu z generacją i walidacją, nie samą latencją po stronie dostawcy. Nie wyliczano ceny pieniężnej; użycie tokenów pochodzi z odpowiedzi API.

Model utworzył:

- Tytuł: **Dostawa dla Dyrekcji**.
- Cel: „Zbierz chip z danymi na wschodniej stronie ulicy”.
- Akcje: wyłącznie `create_quest` i `place_object`.
- Obiekt: `director_package`, etykieta „Pakiet Dyrekcji”, wygląd `data_chip`, miejsce `east_side`.
- Warunek ukończenia: `collect_object`, cel `director_package`.
- Komunikat ukończenia: „Dziękujemy! Chess Corp docenia Twoją efektywność.”

Pełny zwrócony plan, metryki i wynik walidacji: [live-result.json](evidence/live-result.json). Zapis nie zawiera nagłówków, sekretów, tokenów logowania, identyfikatora sesji ani prywatnej historii.

## Weryfikacja

| Faktycznie wykonane sprawdzenie | Wynik |
|---|---|
| `.venv\Scripts\python.exe -m pytest -q` przed testem API | **75 passed**, 20,14 s; jedno znane ostrzeżenie Starlette dotyczące przyszłej migracji TestClient z httpx na httpx2 |
| Budowa izolowanej wersji Compose | Powodzenie; istniejąca budowa pygbag, część etapów z cache |
| Pierwszy quest w przeglądarce | WASD/E/Enter: Buddy → terminal → Buddy; identyfikator odebrany, trzy etapy zaliczone |
| Automatyczna generacja | Jedno rzeczywiste zapytanie po pierwszym queście; Inspector 1/200 wpisów |
| Walidacja i zastosowanie planu | Backend zaakceptował JSON; klient zaakceptował plan i pokazał quest z dostawcą META |
| Obiekt | Nośnik widoczny po prawej stronie sceny, zgodnie z `east_side` |
| Ukończenie | Gracz przeszedł w prawo i nacisnął E; obiekt zniknął, HUD pokazał „UKOŃCZONE: Dostawa dla Dyrekcji” oraz komunikat modelu |
| AI Inspector w przeglądarce | Logowanie właściciela, rzeczywisty payload, model, tokeny, HTTP 200, JSON i `valid=true` |
| Kontrola liczby wywołań | Odczyt API Inspectora: dokładnie 1 Director, 0 Buddy; jeden komunikat blokady `attempted=1 paid_permission=false` |
| Stan końcowy 8080 | Oba kontenery healthy; Buddy `meta`, Director `mock`, `director_paid=false` |

Weryfikacja rozgrywki odbyła się w przeglądarce wbudowanej, na niezmienionym kliencie gry. Nie manipulowano stanem gracza ani zadania przez JavaScript. Walidacja klienta i deterministyczny warunek ukończenia działają dokładnie tak jak w POC 03 mock.

Dowody:

- [Quest Meta aktywny](evidence/quest-meta-active.png).
- [Quest Meta ukończony — pełny widok](evidence/quest-meta-completed.png).
- [Quest Meta ukończony — obszar gry](evidence/quest-meta-completed-canvas.png).
- [Inspector — rzeczywiste metryki](evidence/inspector-meta-metrics.png).
- [Inspector — JSON i walidacja](evidence/inspector-meta-validation.png).
- [Potwierdzenie blokady kosztów](evidence/cost-guard.txt).

## Stan po teście i uruchomienie

1. Jednorazowa blokada zamknęła płatną zgodę natychmiast po próbie, także na wypadek błędu walidacji.
2. Eksportowano bezpieczne wyniki Inspectora i zrzuty przed zamknięciem instancji.
3. Izolowana konfiguracja testowa została zmieniona na `DIRECTOR_ALLOW_PAID_REQUESTS=false`, a kontenery `chess-director-live` oraz ich sieć usunięte przez Compose down. Port 8081 nie pozostaje dostępny.
4. Zwykły backend 8080 sprawdzono poleceniem `Settings.from_env()` wewnątrz kontenera: Buddy `meta`, Director `mock`, zgoda Directora `false`. `.env` również zawiera jawne `DIRECTOR_ALLOW_PAID_REQUESTS=false`.
5. Nie zmieniono źródeł gry ani Buddy’ego, grafik i pierwszego questu. Nie wykonano commita.

Zwykłe uruchomienie nadal:

```powershell
cd C:\Users\piotr\projects\hakaton_meta\chess-corp-poc-codex
docker compose up --build -d
```

Gra: http://localhost:8080. Inspector: http://localhost:8080/admin. Director domyślnie mock, Buddy zachowuje poprzednią konfigurację Meta. Kolejny rzeczywisty test Directora wymaga nowej zgody użytkownika i świadomego włączenia jego osobnej flagi.

## Ograniczenia

- Jest to jeden pomyślny przykład, a nie pomiar niezawodności na wielu generacjach. Nie wykonywano kolejnego płatnego zapytania.
- Test nie dowodzi braku możliwych przyszłych błędów treści lub schematu. Odpowiedź tego testu nie wymagała poprawki ani ponowienia.
- Historia Inspectora jest RAM. Po zamknięciu izolowanego testu żywy wpis zniknął; dowodem pozostają eksport i zrzuty. Nie przenoszono go jako sztucznego wywołania do Inspectora na 8080.
- Zachowano istniejące grafiki i ich kadrowanie; nie przygotowywano nowych zasobów. Nie dodano Guarda, audio ani spacerowania NPC.

## Następny najmniejszy krok

Przygotować demonstrację z odtwarzaniem zapisanego, zatwierdzonego planu bez kolejnych kosztów albo ustalić następny scenariusz. Dalsze płatne generacje nie są obecnie włączone.
