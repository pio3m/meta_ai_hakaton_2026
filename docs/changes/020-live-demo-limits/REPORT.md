# Raport 020 — płatny profil do nagrania demo

Na wyraźne polecenie użytkownika ustawiono lokalny `.env`: Buddy, Quest Director, World AI i obrazy w trybie META, wszystkie właściwe zgody płatne włączone.

| Ustawienie | Wartość |
|---|---:|
| World AI: próby na sesję | 100 |
| World AI: próby globalnie, łącznie z już zużytymi | 1000 |
| World AI: budżet tokenów | 5 000 000 |
| World AI: maksymalna odpowiedź | 4096 tokenów |
| World AI: minimalny odstęp | 20 s |
| Obrazy: limit generacji | 1000 |
| Nowe zlecenia: limit generacji | 1000 |
| Historia rozmów backendu | 30 par |
| Timeout tekstowego API | 30 s |

Podniesiono zakresy walidacji ustawień i limit klienta, który wcześniej kończył planowanie po maksymalnie 10 wywołaniach. Sztywne 50 prób zleceń zastąpiono jawnym `SESSION_JOBS_GLOBAL_LIMIT`, przekazywanym przez Compose. Domyślne konfiguracje pozostają mock i bez zgód płatnych; profil LIVE jest ustawieniem lokalnym użytkownika, bez sekretów w dokumentacji.

Kontenery przebudowano i zrestartowano na porcie 8080. Efektywne ustawienia odczytano wewnątrz działającego backendu bez ujawniania klucza. Nie zerowano ani nie edytowano liczników kosztów. Wynik porównania chronionych plików: `evidence/ledger-check.json`.

Pełny pytest: **308 passed**, jedno wcześniejsze ostrzeżenie deprecacji Starlette/httpx. Log: `evidence/pytest.txt`. Płatnych wywołań testowych nie wykonywano. Nie uruchamiano rozgrywki w przeglądarce, żeby nie zużywać prób przed nagraniem.

Otwórz http://localhost:8080/ i odśwież przez Ctrl+F5. Odpowiedzi i walidację obserwuj w /admin albo wydzielonej sesji /admin/jury. Grafiki nadal generuje się ręcznie w adminie — samo odświeżenie nie regeneruje wszystkich assetów. Limity są wysokie, ale skończone; fallback na awarię API i odstępy między wywołaniami pozostają aktywne. Nie wykonano commita.
