# Raport 015 — cyber-szczury, kontrakty i Nyx

Data: 2026-11-04. Status: zakończony i zweryfikowany. Etap finałowy Chess Corp. Kontynuacja istniejącego projektu, bez nowego frameworka, bazy ani usługi.

## Co działa

**Oba uzgodnione elementy są grywalne:** walka ze szczurami za kredyty oraz nowa handlarzyni Nyx z grafiką wygenerowaną przez Meta.

Zachowano ulicę, oryginalny bar Cybroschligger, kryjówkę hakerów i lobby korporacji. Żadnego oryginału w grafika/ nie nadpisano. Aktualna inwentaryzacja obejmuje 476 obrazów: nazwy, formaty, wymiary, kanał alfa i liczbę klatek znajdują się w [asset-inventory.json](evidence/asset-inventory.json). Wśród zasobów były grafiki sklepu, ale nie gotowy szczur; wykorzystano istniejące sceny i UI, a dwa nowe sprite’y wygenerowano za zgodą użytkownika.

### Kontrakty i walka

- Barman w barze przyjmuje interakcję E. Pierwszy kontrakt umieszcza 3 szczury w zatwierdzonych punktach ulicy; każdy ma 2 HP. Łup 2 KR/szt., wypłata 30 KR po powrocie: łącznie 36 KR.
- Kolejna rozmowa po wypłacie uruchamia drugi kontrakt: 5 szczurów po 3 HP, łup 3 KR/szt. i wypłata 60 KR.
- Spacja wykonuje cios; przytrzymanie powtarza go co 0,32 s. Silnik sprawdza kierunek, zasięg i głębokość. Jest błysk trafienia, odrzut, łuk ciosu, pasek HP przeciwnika oraz liczby obrażeń/łupu.
- Szczury lokalnie patrolują, zbliżają się do gracza i gryzą. Nie są osobnymi agentami LLM. NPC przyjaźni nie otrzymują obrażeń.
- H zużywa apteczkę i przywraca do 45 HP. Po pokonaniu gracza Enter przywraca HP i pozycję za maksymalnie 5 KR. Zabite szczury, questy i wyposażenie pozostają zachowane.
- Walka zatrzymuje się w rozmowie, sklepie, mapie, zagadce, podczas przejścia i poza ulicą.
- Nagrody są jednorazowe, kontrakty mają stałe identyfikatory, sklep nie pozwala kupować za darmo ani wielokrotnie otrzymywać ulepszenia. Stan utrzymuje się podczas podróży. R lub odświeżenie strony zaczyna nową grę.

### Nyx i sklep

Nyx ma własną osobowość, cel, nastrój, pamięć, pozycję i lokalne akcje. Jest trzecim autonomicznym NPC baru, obok Barmana i Gościni. Zatrzymuje się przy graczu. E otwiera sklep; góra/dół wybiera, Enter/E kupuje, Esc zamyka.

| Przedmiot | Cena | Działanie |
|---|---:|---|
| Apteczka | 8 KR | +45 HP przez H; 3 sztuki w sklepie |
| Pałka impulsowa +1 | 18 KR | Obrażenia ciosu 1 → 2; jeden zakup |
| Pancerz uliczny | 22 KR | Maksymalne HP 125, ugryzienia słabsze o 3; jeden zakup |

Nowe kontrakty i ceny są świadomie deterministycznymi danymi content/adventure.json. Nie przedstawiamy ich jako zadań wymyślonych przez Quest Directora. Dotychczasowy Director nadal obsługuje COLLECT, SEQUENCE i LOGIC_PUZZLE.

## Prawdziwe generacje Meta

Wykorzystano istniejący endpoint Meta /images/generations i model muse-image-1.0; nie zmieniano dostawcy. Rejestr generatora ma teraz trzy zamknięte identyfikatory: dawny hacker_emblem oraz cyber_rat i merchant. Każdy ma trwały znacznik jednej płatnej próby. Globalny limit uwzględnia wcześniejszy poster, dlatego w tym etapie dopuszczono tylko dwa nowe obrazy. Generowanie nie uruchamia się przy starcie gry.

| Nowy asset | Wynik | Oryginał API → plik gry | Czas | Tokeny raportowane przez API |
|---|---|---|---:|---:|
| cyber_rat | META, sukces | 1600×1600 → 80×48 RGBA | 13,173 s | 5401 |
| merchant / Nyx | META, sukces | 1600×1600 → 64×96 RGBA | 14,449 s | 5379 |

Zielone tło wskazane w promptach usunięto przez chroma key, obiekt wykadrowano i dopasowano nearest-neighbor. Cztery pliki klatek każdego assetu są lokalną animacją pionowego kołysania, nie czterema osobnymi płatnymi generacjami ani pełnym anatomicznym cyklem chodu. Wszystkie kolejne szczury korzystają z tej samej grafiki.

Pliki publiczne to PNG i manifesty public.json. Prompty/metadane prywatne, znaczniki wydatków i .env są ignorowane przez Git i wykluczone z paczki WWW. Kontrola rzeczywistego archiwum wykazała 56 plików i 0 plików prywatnych: [web-package-check.json](evidence/web-package-check.json).

Dowody: [wyniki dwóch generacji](evidence/asset-results.json), [podgląd Nyx w Inspectorze](evidence/live-inspector-merchant.png).

## World AI LIVE — rzeczywiste wyniki

W izolowanym Compose na 8082 wykonano **dokładnie 3 płatne wywołania World AI**. Wszystkie zwróciły poprawny JSON, przeszły walidację backendu i klienta. Buddy: 0 płatnych. Quest Director: 0 płatnych. Nowe obrazy: 2 płatne generacje. Nie regenerowano dawnego posteru.

| Scena | Model | Wejście | Wyjście | Razem | Czas |
|---|---|---:|---:|---:|---:|
| Ulica, pierwszy plan | muse-spark-1.3 | 1750 | 655 | 2405 | 8,924 s |
| Bar, kontekst aktywnego kontraktu | muse-spark-1.3 | 2648 | 646 | 3294 | 9,294 s |
| Ulica, końcowa sesja jury | muse-spark-1.3 | 1750 | 1265 | 3015 | 16,336 s |
| **Suma World AI** | | **6148** | **2566** | **8714** | |

Model rzeczywiście wybrał WAIT, PATROL, MOVE_TO, INSPECT_TERMINAL, TALK_TO oraz REACT_TO_PLAYER. W barze nadał Nyx cel „Przygotować sprzęt dla łowcy szczurów”, wybrał MOVE_TO bar_market i reakcję na gracza. Telemetria potwierdziła ukończone MOVE_TO Nyx, reakcję Barmana, zbadanie lady i rozmowę Gościni z Barmanem. Reakcja Nyx w tym planie wygasła przed ukończeniem, co Inspector prawidłowo oznaczył jako expired; nie zaliczamy jej jako ukończonej. Na ulicy potwierdzono m.in. ruch i zbadanie terminala przez Hackera oraz WAIT/reakcję Buddy’ego.

[Pełne wyniki bez sekretów](evidence/live-results.json) obejmują walidację, usage, wygenerowane plany, kontekst testowej gry i wykonanie. [Inspector World](evidence/live-inspector-world.png) pokazuje model i metryki; [widok jury](evidence/live-inspector-jury.png) pokazuje tylko jego sesję. Sprawdzono, że jury nie otrzymuje pełnego payloadu ani identyfikatorów innych sesji.

Pierwsze uruchomienie testu miało zbyt krótki czas oczekiwania na raport gry. Opłacony wynik zachowano i odczytano z cache, bez ponownej generacji. Jedno późniejsze żądanie zatrzymał WORLD_MIN_INTERVAL przed HTTP do Meta: nie było płatne. Nie ponawiano go automatycznie. Zmieniono harmonogram klienta na pełny odstęp po odebraniu odpowiedzi i dodano test wolnej odpowiedzi. Trzecią płatną próbę wykonano jawnie w nowej kontrolowanej sesji. Kontenery izolowanego testu zostały usunięte, licznik i dowody zachowane.

Według [oficjalnego cennika Meta](https://dev.meta.ai/docs/pricing-rate-limits), sprawdzonego 2026-11-04: Spark Standard 1,25 USD/mln wejścia i 4,25 USD/mln wyjścia; obraz 0,01 USD/szt. Szacunek tego etapu bez rabatów cache i kredytów: **0,01859 USD World AI + 0,02 USD obrazy = 0,03859 USD**. To oszacowanie z usage, nie odczyt faktury. 10780 tokenów obrazowych jest informacyjne i nie jest drugi raz doliczane do kosztu tekstowego.

## Koszty i konfiguracja końcowa

Zgodnie z najnowszym poleceniem odblokowania płatnego World AI lokalny finał korzysta z META, a nie z domyślnego mocka. Obowiązują: 6 planów/sesję, 12 płatnych prób globalnie dla etapu 015, odstęp co najmniej 30 s, maksymalnie 2400 tokenów odpowiedzi i budżet 150000 tokenów.

Trwały licznik w assets/generated/.world-ai-stage-015.json zawiera 3 próby i 8714 tokenów z testów. Daje to do 9 dalszych płatnych prób przed wykorzystaniem globalnego limitu. Restart ani R nie zerują tego licznika. Nie usuwać pliku, aby nie odnawiać budżetu. Po limicie, błędzie lub niedostępności działa jawnie oznaczony FALLBACK. Brak automatycznych retry po błędzie HTTP.

Generowanie kolejnych obrazów jest wyłączone; gotowy cache Meta pozostaje dostępny. Buddy i Quest Director pozostają w mocku z wyłączonymi zgodami. Domyślne ustawienia w .env.example nadal są mock/false. Płatne testy nie mają ukrytych wywołań Buddy’ego ani Directora.

## Testy i regresje

- Bazowo przed zmianą: **255 testów zaliczonych**.
- Końcowo: **274 testy zaliczone**, jedno ostrzeżenie deprecacyjne FastAPI/Starlette o narzędziu testowym httpx. [Log](evidence/pytest-final.txt).
- Natywny Pygame wykonał 12 klatek bez błędu; [zrzut](evidence/native-final.png). Windows Python 3.13.3 / pygame-ce 2.5.8.
- Docker Compose i pygbag 0.9.3: build zaliczony. W przeglądarce rzeczywisty Python 3.12 / pygame-ce WASM 2.5.7, ten sam zweryfikowany pakiet runtime. [Log budowania](evidence/docker-build.txt).
- Chrome, klawiatura, bez podmiany stanu gry i bez fałszywych odpowiedzi modelu: pierwszy quest, 3+5 szczurów, obie wypłaty, apteczki, pałka i pancerz rzeczywiście ukończone. [Przebieg](evidence/browser-playthrough.json), [oba kontrakty i pancerz](evidence/browser-armor-and-both-contracts.png).
- Drugi przebieg końcowego HUD: ponownie ukończony pierwszy quest, **COLLECT** (backend replay potwierdził completed), kontrakt 3 szczurów, wypłata, zakup pałki, wejście do kryjówki i lobby oraz powroty z zachowaniem stanu. [COLLECT](evidence/final-browser-collect.png), [stan przebiegu](evidence/final-browser-results.json).
- Ten drugi test wykrył 404 telemetrii starszego planu po zmianie lokacji. Naprawa wiąże raport z istniejącym planem w buforze 200, jego sesją i lokacją; cudza sesja/lokacja nadal jest odrzucana. Dodano test regresji i osobny test przeglądarkowy po naprawie.
- Po naprawie osobny test Chrome zakończył się sukcesem: wszystkie 4 lokacje, powroty i raporty wcześniejszych planów bez błędów HTTP, czytelne zlecenie Barmana oraz odrzucony zakup bez kredytów. [Wynik](evidence/targeted-browser-results.json), [zlecenie](evidence/verified-barman-offer.png), [sklep bez darmowych zakupów](evidence/verified-shop-no-free-item.png).
- Poprawiono także priorytet jawnej rozmowy: automatyczne przywitanie pobliskiego NPC nie może nadpisać zlecenia Barmana.
- SEQUENCE i LOGIC_PUZZLE są objęte regresją automatyczną. W tym etapie nie powtarzano ich pełnego przejścia klawiaturą w przeglądarce; nie przedstawiamy dawnych testów jako nowych.

## Uruchomienie i pokaz

1. W katalogu projektu wykonaj `docker compose up --build -d`.
2. Otwórz świeżą kartę http://localhost:8080 i kliknij Graj. Stare uruchomione karty mają stary kod WASM i należy je zamknąć.
3. WASD: ruch; E: rozmowa/obiekt; F: oznaczone drzwi; Spacja: cios (można trzymać); H: apteczka; Tab: mapa; Esc: zamknięcie; R: nowa gra.
4. Idź prawymi drzwiami do BARU. Porozmawiaj z Barmanem przez E, wróć lewymi drzwiami na ulicę i pokonaj szczury. Wróć do Barmana po wypłatę. Nyx stoi po prawej w barze: E otwiera sklep. Pierwszy quest nie jest warunkiem kontraktu.
5. W drugim oknie otwórz http://localhost:8080/admin. Właściciel używa istniejącego ADMIN_TOKEN z .env. Dla jury utwórz nową sesję i jej link gry; osobny profil/incognito loguje się pod /admin/jury tokenem jury.
6. Inspector pokazuje aktualną lokację, NPC, kontekst kontraktu i ekonomii, plan, walidację i wykonanie; assety Meta pokazuje z podglądem. „cache” nie oznacza nowego wydatku.
7. Aby wrócić do gry bez opłat, ustaw WORLD_AI_MODE=mock i WORLD_AI_ALLOW_PAID_REQUESTS=false w .env oraz odtwórz backend/game przez Compose. Gry i gotowych obrazów nie trzeba przebudowywać z tego powodu.

Lokalnie: `uv run python main.py` lub `.venv\Scripts\python.exe main.py`. Dla pełnej pracy z API korzystaj z Compose. CHESS_CORP_WORLD_NETWORK=false wyłącza lokalnego klienta planowania; mechanika walki i lokalne NPC pozostają grywalne.

## Ograniczenia

- To dwie skończone fale i prosty sklep, nie pełny system ekonomii ani generator dowolnych potworów. Kontrakty/obrażenia/ceny kontroluje silnik; Meta wybiera zachowania NPC i wygenerowała dwie grafiki.
- Animacje nowych sprite’ów są proste. Brak nowych dźwięków, rozbudowanego pathfindingu i kolizji z każdym dekoracyjnym meblem.
- Stan kampanii trwa w bieżącej karcie; odświeżenie/R go resetuje. Nie dodano zapisu do bazy.
- Telemetria wykonania pochodzi z klienta i jest walidowana względem planu; nie jest serwerowym systemem anty-cheat.
- Trwały licznik kosztów zakłada jeden backend/worker, jak w obecnym Compose. Nie uruchamiać równocześnie kilku niezależnych procesów META ze wspólnym plikiem licznika.
- Historia 200 wywołań Inspectora pozostaje w RAM; znika po restarcie. Dowody LIVE są zachowane w dokumentacji, a generacje obrazów w trwałym cache.

Nie wykonano commita — w najnowszym zleceniu nie było takiej prośby.


## Następny najmniejszy krok

Otworzyć świeżą kartę gry i nową sesję jury, wykonać pierwszą deratyzację oraz pokazać podgląd Nyx i rzeczywistą decyzję World META w Inspectorze. Kolejna decyzja zużyje jedną z dziewięciu pozostałych prób globalnego budżetu etapu, więc nie resetować licznika.
