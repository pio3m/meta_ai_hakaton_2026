# Raport 019 — lokalizacja EN / PL

## Cel i zakres

Przygotowanie gry i widoku jury do prezentacji po angielsku, z zachowaniem polskiej wersji. Zmiana dotyczy prezentacji oraz instrukcji języka w istniejących promptach. Nie zmieniono mechanik, oryginalnych grafik, audio, kontraktów JSON generowanych przez AI ani konfiguracji kosztów.

## Obsługa

- Gra: EN przy pierwszym uruchomieniu. Kliknij **EN / PL** w lewym górnym rogu albo użyj **F2**, także podczas rozmowy, w sklepie i dzienniku.
- Wybór jest przechowywany w localStorage przeglądarki. Nie zmienia się przy przejściach między lokacjami i pozostaje po odświeżeniu.
- `/admin/jury`: domyślnie EN, własny przełącznik. `/admin`: domyślnie PL, własny przełącznik. Preferencje paneli i gry są niezależne.
- Odśwież stronę po przebudowaniu kontenerów. Dotychczasowy sposób uruchomienia: `docker compose up --build -d`, następnie http://localhost:8080/.

## Implementacja

Wspólny katalog `content/i18n/catalog.json` obsługuje stałe teksty oraz szablony z liczbami, cenami i postępem. Python i przeglądarka korzystają z tych samych tłumaczeń. Lokalizowane są HUD, sterowanie, dialogi fabularne, wskazówki wejść, mapa, sklep Nyx, kontrakty, obrażenia, leczenie, nagrody, błędy, dziennik zleceń i zagadki arytmetyczne.

Buddy/NPC, Quest Director, World AI i nowe zlecenia sesji dostają instrukcję wybranego języka. Dla World AI język przekazuje nagłówek żądania, bez dodawania pola do zamkniętego schematu planu lub snapshotu. Identyfikatory, enumy, pozycje i warunki ukończenia pozostają niezmienione. Wszystkie plany nadal przechodzą istniejącą walidację.

Tryb mock zleceń sesji zwraca dwa jawnie symulowane zadania, bez rezerwacji płatnej próby. Pozwala to testować angielski dziennik bez sieci Meta. Nie zastępuje odpowiedzi w trybie META.

Historia rozmów ma informację o języku źródłowym odpowiedzi. Plan zwraca metadane języka poza JSON-em modelu. Starsze dane bez metadanych są oznaczane jako język nieustalony. W Inspectorze pochodzenie tekstów NPC jest ustalane z zapisanych, zwalidowanych planów tej samej sesji; cudze sesje nie są używane. Treści AI pozostają oryginałem, również po zawinięciu tekstu na kilka linii. Nie ma dodatkowego tłumaczącego wywołania LLM.

## Weryfikacja

- Pełny pytest: **308 passed**, 1 ostrzeżenie deprecacji Starlette/httpx, bez błędów. Log: `evidence/pytest.txt`.
- Natywne Pygame CE: 12 wyrenderowanych klatek z lokalizacją EN, bez uruchamiania World AI; osobny audyt modalnych ekranów SEQUENCE, LOGIC_PUZZLE, sklepu, mapy, kontraktu i porażki.
- Audyt sprawdzonych ekranów nie zgłosił nieprzetłumaczonych stałych tekstów (`evidence/render-untranslated.json`).
- Docker: przebudowanie frontendu pygbag i backendu FastAPI. Składnia obu skryptów lokalizacji i Inspectora sprawdzona przez Node.
- Chrome / prawdziwa gra, sterowanie klawiaturą: pierwszy quest ukończony w EN; ulica → bar → ulica, kontrakt na 3 szczury, walka, odebranie nagrody i zakup apteczki u Nyx; kryjówka → ulica → lobby → ulica; mapa, mock rozmowy z Barmanem i dwa mock zlecenia sesji. Stan pierwszego questu oraz portfela/ekwipunku zachowany między lokacjami.
- EN → PL → EN sprawdzone w grze i sklepie. Widok jury otwarty po angielsku z aktywną sesją demonstracyjną.
- Osobne końcowe sprawdzenie przebudowanej wersji obejmuje zapamiętanie języka po odświeżeniu, kliknięcie widocznego przełącznika, sklep, rozmowę i angielskie stany kart NPC. Wynik: **PASS**, brak błędów API i przeglądarki; `evidence/browser019-final.json`.

Dłuższy scenariusz zakończył ścieżkę rozgrywki i jury, po czym jego natychmiastowa asercja skrótu F2 nie poczekała na klatkę SDL. Poprawiono oczekiwanie w teście i sprawdzono trwałość osobnym scenariuszem. Test myszy wykrył rzeczywisty błąd współrzędnych przy CSS letterboxingu; przełącznik ma teraz hit-test widocznej zawartości canvasu. Kontrola zrzutów wykryła też brak tłumaczeń nazw sklepu z prefiksem wyboru oraz stanu NPC z dopisanym źródłem — poprawiono złożone etykiety i dodano regresje.

Zrzuty w `evidence/`: ulica, dziennik, dialog Buddy'ego, pierwszy quest, kontrakt, walka, zakup, kryjówka, lobby, mapa i jury. Pliki `final-*` pokazują wersję po ostatnich poprawkach etykiet; wcześniejsze zrzuty dokumentują przebieg testu.

## Koszty i bezpieczeństwo

**0 płatnych wywołań, 0 tokenów Meta w tych testach.** Test przeglądarkowy działał na osobnym Compose pod portem 8084, z pustym kluczem, trybami MOCK, wszystkimi zgodami płatnymi wyłączonymi i bez montowania produkcyjnych liczników. Produkcyjny port 8080 i konfiguracja trybów nie były używane do rozgrywki testowej.

Sumy kontrolne `.env`, `compose.yaml`, licznika World AI i licznika zleceń sesji są porównane z początkiem etapu w `evidence/protected-check.json`. Nie zerowano liczników. Nie uruchamiano generacji obrazów ani płatnych testów Buddy'ego lub Directora.

## Ograniczenia i pozostawione oryginały

- Historyczne odpowiedzi AI, wspomnienia i opisy z innego języka mogą nadal zawierać polski. Są oznaczone `[PL original]` albo jako oryginał o nieustalonym języku; nie są przedstawiane jako angielskie tłumaczenie. Nowe żądania otrzymują właściwy język.
- Surowe prompty, wyniki i snapshoty JSON pozostają danymi źródłowymi. Mogą zawierać polską treść historyczną; technicznych identyfikatorów i enumów nie tłumaczono.
- Oryginalnych napisów w bitmapach i nazw własnych nie przemalowywano. Grafiki pozostają oryginalne.
- Nie wykonywano testu językowego prawdziwego modelu Meta zgodnie z zakazem płatnych wywołań. Sprawdzono lokalne prompty, mocki i walidację, bez obietnicy, że model nigdy nie odpowie w innym języku.
- Nie wprowadzono zapisu postępu gry po odświeżeniu. Wymagane zapamiętanie dotyczy języka; stan questu jest zachowywany przy zmianach lokacji.

Następny najmniejszy krok: nagranie przebiegu EN na przygotowanej sesji jury. Nie wykonano commita — nie było takiego polecenia.

## Gotowa instancja

Kontenery na porcie **8080** zostały odtworzone z nowymi obrazami, z zachowaniem istniejących ustawień META. Osobną instancję mock 8084 zatrzymano i usunięto. Kontrola HTTP health, strony gry, katalogu tłumaczeń i jury: 200. Nie uruchamiano rozgrywki na produkcyjnej instancji podczas tej kontroli. Wszystkie cztery chronione sumy kontrolne pozostały zgodne z początkiem etapu.
