# CHESS CORP — Living World Expansion

Data: 2026-11-04. Status: grywalne demo uruchomione na http://localhost:8080. Test LIVE zakończony w zatwierdzonym limicie, płatne wywołania ponownie wyłączone.

## Cel i wynik

Połączono istniejącą ulicę z **trzema** dodatkowymi grywalnymi lokacjami. Bar nie został usunięty ani zastąpiony: używa oryginalnego wnętrza oraz sprite’ów barmana i gościni z `grafika/Bar/`. W świecie działa łącznie 10 ruchomych postaci. Gracz odwiedza lokacje, rozmawia, korzysta z terminali i wraca do tego samego questu oraz ekwipunku.

Muse Spark 1.3 rzeczywiście wygenerował trzy poprawne plany: jeden dla ulicy i dwa dla baru. W barze zrealizowano ruch gościni, rozmowę z barmanem i reakcję barmana na gracza; widoczna była wypowiedź pochodząca z modelu. Muse Image 1.0 wygenerował jeden neonowy emblemat, który został przetworzony, zapisany w cache i pokazany w kryjówce w przeglądarce. Nie podstawiano mocka za rzeczywiste odpowiedzi.

## Inwentaryzacja i zachowanie zawartości

Przed zmianą zinwentaryzowano 476 obrazów i animacji: ścieżki, rozdzielczości, formaty, tryby i liczbę klatek. Wynik: [asset-inventory.json](evidence/asset-inventory.json); wybrane materiały: [arkusz podglądowy](evidence/asset-contact-sheet.png).

W kodzie istniała jedna grywalna scena ulicy. Istniejący bar był kompletnym zestawem oryginalnych zasobów: `Bar.png`, tło, lada, barman, goście, stoliki, krzesła i hologramy. Wykorzystano ten zestaw, zamiast projektować bar od nowa. Nie zmieniono żadnego pliku w `grafika/` ani dotychczasowych klatek gracza i tła ulicy.

- Bar: oryginał 1920×1080 zmniejszony do 960×540 przez nearest-neighbor. Wybrano i sprawdzono komórki arkuszy barmana (2×3, komórka 288×240) i gościni (3 kolumny, wysokość komórki 324); pochodne klatki mają wspólny punkt podparcia.
- Kryjówka: wykorzystuje oryginalny pas pokoju `Trailer/MC_Room.png`, prostą podłogę i oryginalny hologram jako fallback dekoracji.
- Lobby: używa istniejącej architektury `Background/Tło.png` oraz prostej recepcji i terminala narysowanych w pasującej palecie.
- Nowy obraz Meta: oryginalna odpowiedź miała 1600×1600 PNG. Backend przetworzył ją do 64×64 i powiększył nearest-neighbor do 128×128, zachowując czytelny pixel art. To nie jest zamiennik oryginalnej grafiki baru.

## Lokacje i mechaniki

| Lokacja | NPC | Interakcja | Dostęp z ulicy |
|---|---|---|---|
| Ulica Chess Corp | Buddy, Security, Hacker, Employee | dotychczasowy quest, Buddy chat, questy Directora | centrum świata |
| Bar Cybroschligger | Barman, Gościni | rozmowy, obsługa gości, rachunek/napój przy ladzie | prawe drzwi BAR |
| Kryjówka hakerów | Cipher, Kontakt | rozmowa, odczyt archiwum, fragment danych; dekoracja Meta | lewe drzwi KRYJÓWKA |
| Lobby korporacji | Recepcja, Ochrona | rejestr wizyty, przepustka, patrol | drzwi LOBBY po prawej od centrum |

**F** przy drzwiach przenosi do lokacji i z powrotem. **E** pozostaje rozmową lub interakcją; rozdzielenie tych klawiszy chroni questy, których obiekty mogą pojawić się blisko wejść. Przejście trwa 0,44 s, ma fade i krótką nazwę miejsca. **Tab** otwiera mapę. WASD, Enter, Esc i R pozostają dostępne.

Przejście nie wywołuje resetu gry. Zachowane są obiekty Quest, Chat i Game Director, ekwipunek, historia rozmów, instancje NPC, ich pamięć i kolejki zachowań. Nowe przedmioty nie udają identyfikatora pracownika; UI sprawdza konkretnie `employee_badge`. NPC w nieaktywnej scenie nadal mają lokalne aktualizacje; ich pozycje nie są tworzone od nowa po powrocie.

Postacie zatrzymują się w zasięgu rozmowy, odwracają i czekają na odejście gracza, zgodnie z poprzednią zmianą. Barman patroluje ladę i stoliki oraz obsługuje gości; Cipher pracuje przy terminalu; ochrona obchodzi lobby. Interakcja wybiera bliższego rozmówcę lub obiekt. Nowe postacie mają krótkie dialogi lokalne; swobodny chat tekstowy nadal dotyczy Buddy’ego. Nie wykonano dodatkowych płatnych rozmów.

## Kontrakty i bezpieczeństwo wykonania

Rozszerzono istniejące moduły, bez nowego frameworka, bazy ani usługi:

- `content/locations.json` i `game/locations.py`: dane, przejścia, widoki i zachowanie instancji lokacji.
- `game/living_world.py`: dotychczasowy executor, wspólny licznik planów klienta, kontekst lokacji i podróży.
- `game/world_contract.py` i `backend/world_models.py`: WorldPlanV1 nadal dotyczy ulicy, WorldPlanV2 wskazuje lokację i dokładny zestaw jej NPC. Te same akcje MOVE_TO, PATROL, WAIT, TALK_TO, INSPECT_TERMINAL i REACT_TO_PLAYER. Schemat wysyłany do modelu ogranicza identyfikatory do aktywnej sceny; backend i klient dodatkowo walidują semantykę.
- `backend/world_ai.py` i `world_routes.py`: istniejący adapter Meta, timeout, idempotencja, walidacja oraz wspólny globalny budżet. Model dostaje cele, profile, stan, krótką pamięć i ostatnie wydarzenia, a nie uprawnienia do zmiany inventory lub wykonania kodu.
- `/api/world/presence`: bezpłatna telemetria. Inspector pokazuje aktywne miejsce także po wyczerpaniu limitu LLM. Stan jest ograniczony w RAM; jury widzi tylko swoją sesję.
- Źródła META / MOCK / FALLBACK są jawne. Lokalna pauza przy graczu i lokalna kwestia nie udają decyzji modelu. Wygenerowany obraz zachowuje źródło META także wtedy, gdy zachowania działają w mocku.

## Meta Image API — dokumentacja i dostępność

Sprawdzono oficjalne [modele Meta](https://dev.meta.ai/docs/models), [generowanie obrazów](https://dev.meta.ai/docs/image-generation) i [POST /images/generations](https://dev.meta.ai/docs/api-reference/images/create-image). Potwierdzają model `muse-image-1.0`, endpoint `https://api.meta.ai/v1/images/generations` oraz wynik `data[].b64_json`.

Dodatkowo rzeczywisty GET `/v1/models` dla skonfigurowanego konta zwrócił HTTP 200 i zawierał Muse Image 1.0 oraz Muse Spark 1.3. Był to odczyt katalogu, nie płatna inferencja. Dowód: [dostępność modeli](evidence/meta-model-availability.json).

`backend/asset_generator.py` implementuje jednorazowy, dostępny tylko właścicielowi endpoint `/admin/api/asset/generate`. Nie generuje obrazów przy starcie. Żądanie ma `n=1`, stały prompt fikcyjnej dekoracji, format PNG/base64 i wyłączone wyszukiwanie oraz narzędzia. Nie zmieniano dostawcy.

Przed HTTP zapisywany jest wyłączny, trwały znacznik jednej próby. Pozostaje po timeoutach, błędach i restartach. Nie ma automatycznego ponowienia. Poprawna odpowiedź jest dekodowana, sprawdzana, przetwarzana i zapisywana atomowo. Kolejne żądanie zwraca cache bez wywołania modelu. W teście rzeczywiste ponowne odczytanie cache nie zwiększyło liczby płatnych wywołań.

Publiczna paczka zawiera tylko PNG i metadane źródła. Pełny prompt oraz znacznik wydatku pozostają lokalnie, poza paczką przeglądarkową i Git. Właściciel Inspectora widzi oryginalny payload historycznej generacji także z cache, z informacją, że teraz nie wywołano modelu. Jury dostaje źródło, model, czas i podgląd, bez pełnego promptu.

## Rzeczywiste wywołania i koszty

Test odbył się w izolowanym Compose na 8082. Buddy i Quest Director miały mock oraz wyłączone zgody. World AI miał limit 3 globalnie i na sesję, minimalny odstęp 30 s, limit wyjścia 1800 tokenów i budżet 50000 tokenów. Klient używa zegara rzeczywistego i sekundy marginesu. Tymczasowa osłona testowa zachowywała liczbę prób na dysku i po trzeciej wyłączała zgodę adaptera. Nie podmieniała payloadów ani odpowiedzi.

| Wywołanie | Model / lokacja | Czas Inspectora | Wejście | Wyjście | Razem | Wynik |
|---|---|---:|---:|---:|---:|---|
| World 1 | muse-spark-1.3 / ulica | 12819,65 ms | 1603 | 997 | 2600 | poprawny JSON v1 |
| World 2 | muse-spark-1.3 / bar | 8106,42 ms | 1798 | 606 | 2404 | poprawny JSON v2 |
| World 3 | muse-spark-1.3 / bar | 6392,50 ms | 1789 | 502 | 2291 | poprawny JSON v2 |
| Asset 1 | muse-image-1.0 / dekoracja kryjówki | 12056,58 ms | 4100 | 1287 | 5387 | PNG zapisany i pokazany w grze |

**Łącznie: 3 płatne World AI i 1 generacja obrazu. World AI: 7295 tokenów; obraz: 5387 tokenów referencyjnych. Buddy: 0; Quest Director: 0.** Wszystkie cztery rzeczywiste odpowiedzi miały HTTP 200. Nie wykonano dodatkowych płatnych prób.

Model sam wybrał:

- Ulica: Buddy WAIT i REACT_TO_PLAYER; Security PATROL; Hacker MOVE_TO do terminala i INSPECT_TERMINAL; Employee MOVE_TO do centrum i TALK_TO z Buddy’m.
- Bar, runda 2: Barman REACT_TO_PLAYER z wypowiedzią „Witaj w Cybroschligger! Siadaj, co polecić?”; Gościni MOVE_TO do stolika i TALK_TO z barmanem.
- Bar, runda 3: Barman REACT_TO_PLAYER oraz INSPECT_TERMINAL; Gościni REACT_TO_PLAYER i TALK_TO z barmanem.

Model wybrał wszystkie sześć rodzajów akcji. Zapisana telemetria potwierdza zakończenie WAIT i REACT_TO_PLAYER na ulicy oraz MOVE_TO, TALK_TO i REACT_TO_PLAYER w barze. Trzecia odpowiedź była poprawna i zapisana, ale w czasie jej nadejścia gracz przechodził do kryjówki; nie deklarujemy osobno potwierdzonego pełnego wykonania tej rundy. Kryjówka i lobby zostały sprawdzone w zachowaniach lokalnych/mock, nie otrzymały osobnego płatnego planu. Nie zwiększano limitu, aby to zmienić.

Według sprawdzonego [cennika Meta](https://dev.meta.ai/docs/pricing-rate-limits), Standard Muse Spark kosztuje 1,25 USD / mln tokenów wejścia i 4,25 USD / mln wyjścia, a obraz 0,01 USD za sztukę. Bez uwzględnienia rabatu cache lub kredytów, szacunek wynosi **0,01543 USD za World AI + 0,01 USD za obraz = około 0,02543 USD**. To oszacowanie według usage i cennika, a nie odczyt rozliczenia konta. Tokeny obrazowe nie są drugi raz doliczane do kosztu tekstowego.

Po próbie osłona zgłosiła `CONNECTED_WORLD_PAID_DISABLED`. Kontenery LIVE zatrzymano i usunięto, a tymczasowe pliki zawierające konfigurację klucza oraz token jury usunięto. W lokalnym .env wszystkie cztery tryby są mock i wszystkie cztery płatne zgody false. Asset pozostaje w cache.

## Weryfikacja wykonana w tym etapie

| Sprawdzenie | Rzeczywisty wynik |
|---|---|
| Testy bazowe przed zmianą | 238 passed; liczba 233 z opisu była historyczna |
| Końcowy pytest | **255 passed**, 1 znane ostrzeżenie Starlette/httpx, 37,66 s |
| 17 nowych przypadków | kontrakty lokacji, brak celów z innych scen, ruch NPC, zatrzymanie i rozmowa, fade, zachowanie referencji sesji, inventory i pamięci, izolacja jury, źródło lokalnej pauzy, generator HTTP fake, cache, limit jednej próby i awarie |
| Native Pygame / SDL dummy | poprawnie wyrenderowano wszystkie cztery lokacje przez tę samą mechanikę przejść |
| Docker / pygbag | budowa końcowa udana; gra i backend healthy na 8080 |
| Przeglądarka: bar | wejście F, ruch postaci, interakcja przy ladzie, bezpośrednia odpowiedź barmana po E w końcowej wersji; prawdziwa wypowiedź barmana z Meta podczas LIVE |
| Przeglądarka: lobby | wejście i wyjście, ruch ochrony, rozmowa z recepcją i rejestr wizyty |
| Przeglądarka: kryjówka | wejście i wyjście, rozmowa z Cipher, terminal archiwum; osobno wariant z oryginalnym hologramem i z obrazem Meta |
| Przeglądarka: zachowanie questu | rozpoczęto pierwszy quest, odwiedzono trzy lokacje i odebrano trzy przedmioty, wrócono po badge i ukończono pierwszy quest |
| Przeglądarka: dynamiczny quest | po podróży ukończono COLLECT, również przy drzwiach kryjówki, bez konfliktu F/E |
| SEQUENCE i LOGIC_PUZZLE | zachowane, przechodzą dotychczasowe testy; nie powtarzano osobnej pełnej rozgrywki przeglądarkowej tych dwóch typów w tym etapie |
| Inspector | model, tokeny, JSON, walidacja i wykonanie; aktywna lokacja oraz asset; zalogowano widok jury, zweryfikowano brak pełnego promptu i pokazano obraz; dostęp wygasł po 30 min zgodnie z polityką |
| Cache realny | drugi odczyt assetu zwrócił cache, 0 dodatkowych wywołań; SHA256 bez zmian |
| Końcowe HTTP / bezpieczeństwo | /, /health, katalog i PNG: 200; po restarcie 0 inferencji, historyczny asset zaimportowany z cache; prywatny manifest i znacznik nie znalazły się w APK |
| Mapa i końcowa wersja | w przeglądarce sprawdzono Tab, nazwy czterech lokacji, zamknięcie mapy i działanie obrazu z cache na 8080 |
| Sekrety i grafiki | skan zmienionych plików pod kątem rzeczywistych skonfigurowanych kluczy i tokenu administratora: czysto; oryginały niezmienione; .env i prywatny cache ignorowane |

Dowody: [rzeczywiste odpowiedzi i wykonanie](evidence/live-results.json), [cache i prywatność](evidence/cache-and-privacy-check.json), [kontrola końcowa](evidence/final-safety-check.json). Pliki zawierają wyłącznie wybrane dane testowego świata, bez kluczy, tokenów logowania, pełnych promptów i prywatnych rozmów.

## Screenshoty

- [Końcowa rozmowa z barmanem na 8080](evidence/final-bar-bartender.png)
- [Końcowa kryjówka z obrazem Meta z cache](evidence/final-hideout-8080.png)
- [Mapa czterech lokacji](evidence/final-map-8080.png)
- [Bar z prawdziwą wypowiedzią Meta](evidence/live-bar-meta.png)
- [Kryjówka z wygenerowanym assetem](evidence/live-hideout-generated-asset.png)
- [Lobby i recepcja](evidence/browser-lobby.png)
- [Kryjówka działająca na oryginalnych assetach](evidence/browser-hideout-original-assets.png)
- [Inspector assetu w widoku jury](evidence/inspector-asset-jury.png)
- [Inspector rzeczywistego World AI](evidence/inspector-world-meta.png)
- [COLLECT ukończony po podróży](evidence/browser-collect-after-world-tour.png)
- [Oryginalny bar i pozostałe assety przed obróbką](evidence/asset-contact-sheet.png)

Natywne zrzuty `local-*.png` pokazują końcowe widoki wszystkich czterech lokacji. Końcowe zrzuty z 8080 znajdują się w tym samym katalogu evidence.

## Uruchomienie i demo jury

1. W katalogu projektu: `docker compose up --build -d`.
2. Otwórz nową kartę http://localhost:8080 i kliknij Graj. Stare uruchomione karty należy zamknąć, aby pobrać nowy kod.
3. WASD: ruch; E: rozmowa/obiekt; F przy oznaczonych drzwiach: podróż; Tab: mapa; Esc: zamknięcie rozmowy/mapy; R: nowa sesja.
4. Ulica: lewe drzwi prowadzą do kryjówki, środkowe prawe do lobby, skrajne prawe do baru. Każda lokacja ma drzwi ULICA przy lewym brzegu. Nie trzeba kończyć pierwszego questu, aby zwiedzać.
5. Drugie okno: http://localhost:8080/admin. Właściciel loguje się istniejącym ADMIN_TOKEN. Utwórz sesję demonstracyjną, użyj jej linku gry i zaloguj osobny profil/incognito pod /admin/jury tokenem jury. Nie pokazuj jury panelu właściciela z pełnymi promptami. Dostęp jury trwa 30 minut.
6. Po restarcie Inspector pokazuje historyczny obraz jako cache, bez generacji. W kryjówce obraz pozostaje dostępny przy wszystkich integracjach mock.
7. Gdy właściciel świadomie uruchamia kolejną ograniczoną prezentację World META: WORLD_AI_MODE=meta, WORLD_AI_ALLOW_PAID_REQUESTS=true, limity 3/3, odstęp 30, max_output_tokens 1800, token_budget 50000. Buddy i Quest Director pozostawić mock z wyłączonymi zgodami. Następnie `docker compose up -d --force-recreate backend game`. Ta konfiguracja uruchamia najwyżej trzy plany na proces, nie nieskończone odpytywanie. Po pokazie wrócić do mock/false i odtworzyć kontenery.
8. Nie trzeba ponownie włączać generacji obrazu. Trwały znacznik jednej próby pozostaje w assets/generated; endpoint nie wydaje drugiej płatnej próby. Sam cache i publiczny PNG mogą być używane bez opłat.

Lokalnie: `.venv\Scripts\python.exe main.py` lub `uv run python main.py`. Bez sieci można ustawić `CHESS_CORP_WORLD_NETWORK=false`; lokalne zachowania i quest startowy działają. W WSL można korzystać z tego samego Compose i przeglądarki Windows; nie przeprowadzono odrębnego testu natywnego okna WSLg.

## Ograniczenia

- To POC: dekoracyjne meble nie mają kompletnego systemu kolizji. Lobby jest prostą aranżacją z istniejącej architektury, a nie nowym kompletnym zestawem wnętrz.
- Tło baru zawiera także statycznych gości oryginalnej ilustracji; autonomiczne są dodatkowe postacie z silnika, nie wszystkie sylwetki narysowane w tle.
- NPC współdzielą część sprite’ów. Nie dodano audio, walki ani rozbudowanego pathfindingu.
- Trzy płatne plany nie zapewniają osobnego planu Meta dla każdej lokacji. Po wyczerpaniu limitu świat pozostaje aktywny lokalnie i jest tak oznaczony.
- Stan gry trwa podczas przejść w bieżącej sesji. Odświeżenie strony i R rozpoczynają nową grę. Nie dodano bazy ani zapisu kampanii na dysku.
- Globalny budżet World AI i historia Inspectora są w RAM jednego procesu; restart zeruje ten licznik, dlatego po testach zgody są false. Cache obrazu i znacznik jego jednej próby są trwałe.
- Telemetria jest raportem klienta sprawdzanym względem planu, a nie niezależną symulacją serwera odporną na oszustwa.
- Ostatnie poprawki napisów i oznaczania lokalnej pauzy sprawdzono w mocku i testach; nie uruchamiano za nie dodatkowej płatnej próby.

## Następny najmniejszy krok

Przed prezentacją otworzyć mapę, grę i świeży widok jury. Jeśli potrzebne są nowe decyzje Meta na żywo, właściciel włącza świadomie kolejną ograniczoną sesję World AI; obraz jest już gotowy i nie wymaga ponownej generacji.
