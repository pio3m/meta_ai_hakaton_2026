# Raport 018 — NPC, walka, rozmowy i nowe questy

Data: 2026-11-04. Status: wdrożone w lokalnym Compose.

## Jak grać

- **Spacja**: atak także bez aktywnego zadania na szczury. Przytrzymaj, aby powtarzać cios. Pałka impulsowa kupiona u Nyx zwiększa obrażenia z 1 do 2.
- **T** przy NPC: tekstowa rozmowa z tą postacią. Enter wysyła, Esc zamyka. Działa dla Buddy’ego, Security, Hackera, Employee, Barmana, Gościni, Nyx, Cipher, Kontaktu, Recepcji i ochrony lobby.
- **E** zachowuje rozmowy fabularne, sklep i interakcje. Przy nowym przedmiocie zbiera go do bieżącego zlecenia.
- **J**: dwa nowe zlecenia tej sesji, lokalizacje przedmiotów, postęp i nagrody. R albo świeże uruchomienie tworzy nową sesję i nowe zapytanie do Directora.
- **F**: drzwi między dotychczasowymi lokacjami. M i dotychczasowe audio pozostają dostępne.

Gra: http://localhost:8080. Otwórz świeżą kartę albo Ctrl+F5, następnie Graj. Po przebudowie oba kontenery były zdrowe. Standardowe uruchomienie: `docker compose up --build -d`.

## Walka z postaciami

Trafienie w zasięgu ciosu prowokuje konkretnego NPC. Postać podchodzi i odpowiada atakiem. Ochrona ma 24 HP i zadaje większe obrażenia; pozostałe postacie 14 HP. Walka jest wykonywana lokalnie i deterministycznie, bez wywołania LLM co klatkę. Trafienia mają efekty i pasek HP.

Po pokonaniu NPC jest ogłuszony przez około 12 sekund, następnie wraca. Nie usuwamy Barmana, Buddy’ego ani Nyx na stałe i nie płacimy kredytów za farmienie postaci fabularnych. Po ratunku gracza agresja jest usuwana. Podstawowe zadanie Buddy’ego zachowuje jego zatwierdzoną strefę na ulicy. Nie można trafiać szczurów znajdujących się w innej lokacji.

## Czat z tożsamością NPC

Wykorzystano istniejącą integrację Meta, Guarda i Inspector. Serwer pobiera rolę, osobowość oraz cel postaci z własnych danych content/world_ai.json i content/locations.json. Identyfikator postaci jest zamkniętą listą, nie dowolnym promptem klienta. Każdy NPC ma oddzielną historię rozmów w sesji: wypowiedzi do ochroniarza nie stają się historią Nyx lub Buddy’ego.

Kontekst obejmuje lokację, nastrój, cel, krótką pamięć oraz informację o agresji i zdrowiu. Nadal jest traktowany jako niezaufane dane, a nie polecenia zmieniające zasady. Czat nie przyznaje przedmiotów, pieniędzy i zaliczeń. Dotychczasowe dialogi E i pierwszy quest działają niezależnie od czatu T.

## Nowy game loop

Nowy endpoint Directora generuje **dwa dodatkowe zlecenia w jednym wywołaniu META na świeżą sesję**. Nie wymaga ukończenia pierwszego dnia. Każde zadanie ma własną treść, przedmiot, 1–2 zatwierdzone miejsca i nagrodę 15–45 KR. Model zwraca wyłącznie JSON, a backend i klient sprawdzają ten sam zamknięty kontrakt. Nie ma wykonywalnego kodu ani dowolnych współrzędnych.

Zbieranie i wypłaty są deterministyczne. Każdy przedmiot można zaliczyć raz, a każdą nagrodę wypłacić raz. Działają wszystkie cztery lokacje; po podróży zachowuje się stan zbierania, wyposażenie i kredyty. Pierwszy quest, wcześniejszy Director COLLECT/SEQUENCE/LOGIC_PUZZLE oraz dwa kontrakty Barmana pozostają dostępne.

Każda nowa sesja ma nowy identyfikator i nonce w zapytaniu: wcześniejszy plan nie jest używany jako plan nowej gry. Powtórne odebranie tego samego już zaakceptowanego planu wewnątrz tej samej sesji to ochrona przed podwójną opłatą, nie powtórzenie dawnych zleceń przy nowym uruchomieniu. Próba generacji nie jest ponawiana automatycznie po błędzie.

Nowy moduł ma trwały limit 50 generacji par zleceń w assets/generated/.session-jobs-spend.json, niezależny od World AI. Licznik nie jest usuwany przez czyszczenie grafik. Jeśli API lub walidacja zawiedzie, dziennik pokazuje niedostępność, a dotychczasowa gra pozostaje grywalna. Nie podstawiamy zlecenia mock jako odpowiedzi Meta.

## Admin: regeneracja i usuwanie zapisanych grafik

Użytkownik wybrał ręczne generowanie grafik w adminie zamiast kosztownej automatycznej generacji przy każdym starcie.

Na /admin właściciel wybiera cyber-szczura, Nyx albo emblemat kryjówki i klika **Wygeneruj nowy asset**. To jedno płatne wywołanie Muse Image z nowym identyfikatorem próby i wariacją promptu. Omija istniejący obraz. Przycisk jest wyłączony podczas oczekiwania, a ten sam identyfikator nie może drugi raz wydać płatnego żądania. Nie ma automatycznych retry. Przed otrzymaniem poprawnego obrazu nie usuwa się ostatniej działającej grafiki.

**Usuń zapisane pliki assetu** usuwa wyłącznie wygenerowane pliki wybranego identyfikatora. Nie usuwa oryginalnych grafik, plików innych assetów, historii gry, kluczy ani trwałych liczników kosztów. Po usunięciu gra korzysta z lokalnej grafiki zastępczej, aż do kolejnej jawnej regeneracji.

Działający klient porównuje lokalnie wersje obrazów około co 10 sekund i pobiera tylko zmienione PNG. To nie są wywołania modelu i nie generuje kosztów API. Nowa grafika pojawia się bez przebudowania Dockera lub przerywania questów. Widok jury nie ma przycisków generowania i kasowania.

Parametr ASSET_AI_GLOBAL_LIMIT wpisany przez użytkownika jako 15 jest teraz obsługiwany; poprzedni twardy zakres do 3 powodował błąd startu. Obsługiwany zakres jest ograniczony do 50. Ręczne regeneracje mają trwały własny licznik i limit z tej konfiguracji, a dawne znaczniki wydatków pozostają nienaruszone. Tryby LLM pozostają META. W tej zmianie nie generowano płatnie żadnego nowego obrazu — przycisk jest do użycia przez właściciela.

## Weryfikacja wykonana

- Wybrane istniejące sprawdzenia backendu, czatu, grafik, audio i lokacji: **58 zaliczonych**.
- Sprawdzenia walki i nowych elementów: **21 zaliczonych**, w tym prowokacja i odwet ochroniarza, ogłuszenie/odzyskanie zdrowia, izolacja historii, jednorazowe nagrody, świeże zapytanie nowej sesji i brak podwójnej opłaty regeneracji. Te sprawdzenia używają atrap HTTP, bez płatnych testów API.
- Pygame wystartował i wyrenderował **12 klatek** bez sieci.
- Docker i pygbag zbudowane; oba kontenery uruchomione.
- Prawdziwy Muse Spark w Chrome wygenerował **dwie misje** w każdej z dwóch świeżych sesji. Nazwy zleceń różniły się. [Podsumowanie](evidence/live-summary.json), [pierwsza sesja](evidence/startup-live-first.json), [druga sesja i czat](evidence/startup-live.json).
- W Chrome postać **Employee** odpowiedziała tekstowo jako pracownik zabiegający o awans, przez prawdziwe META. Przykład odpowiedzi: „Jestem młodszym analitykiem w Chess Corp, dział logistyki i raportów. (…) Celuję w awans (…)”. [Zlecenia w grze](evidence/new-session-jobs.png), [czat NPC](evidence/npc-text-chat.png).
- Pierwszy skrypt poprawnie otrzymał questy, ale nie wysłał wiadomości, bo automatyczne wpisywanie było szybsze niż otwarcie pola tekstowego. Dodano naturalny odstęp klawiaturowy; kolejny przebieg potwierdził czat. Nie przedstawiamy pierwszego przebiegu jako udanego sprawdzenia rozmowy.
- Nie wykonywano długiego pełnego regresyjnego przechodzenia wszystkich dawnych questów ani płatnej regeneracji obrazu. Pełne 284 testy z poprzedniego etapu są wynikiem historycznym, nie nowym wynikiem tej zmiany.

[Log integracji](evidence/checks.txt), [log walki](evidence/combat-checks.txt), [log nowych mechanik](evidence/expansion-checks.txt), [natywny start](evidence/native-ready.png), [build](evidence/build.txt).

## Ograniczenia

To POC: walka ma proste zasięgi i pościg w obrębie lokacji, bez zaawansowanego systemu frakcji. Wypłaty i questy są stanem bieżącej rozgrywki; odświeżenie/R zaczyna nową grę. Model może nawiązywać do podobnych motywów, ale otrzymuje nowe zapytanie, a nie poprzedni plan z cache. Historia Inspectora pozostaje w RAM. Regeneracja obrazów trwa tyle co odpowiedź Meta, a po niej klient może potrzebować do około 10 sekund na lokalną aktualizację.

Następny krok: otworzyć świeżą kartę gry, użyć J i wykonać nowe zlecenie, kupić pałkę, a następnie skorzystać z T przy wybranym NPC. Nie wykonano commita.
