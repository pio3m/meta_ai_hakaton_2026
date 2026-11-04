# Raport — POC 016: Cyberpunk Sound Design

Data: 2026-11-04. Dokumentacja zmiany 017, ponieważ numer 016 zajmuje wcześniejsza poprawka UI. Prace zakończone. Na polecenie użytkownika zakończono dalsze testowanie; poniżej wyłącznie już wykonane sprawdzenia.

## Dodane dźwięki i pochodzenie

Inwentaryzacja nie wykazała istniejących zasobów audio w projekcie, w tym w grafika/. [Wynik](evidence/audio-inventory.json). Oryginalne 476 grafik pozostawiono bez zmian.

Przygotowano lokalnie 14 oryginalnych WAV-ów: cztery ośmiosekundowe ambienty oraz dziesięć efektów. Wszystkie powstały z oscylatorów i deterministycznego szumu w tools/generate_audio.py. Nie użyto cudzych nagrań, sampli, płatnego API audio ani nowych usług/frameworków. Pliki i generator dedykowano CC0-1.0, z możliwością użycia w repozytorium i filmie; nie zmienia to praw do wcześniejszych grafik. [Pochodzenie](../../../assets/audio/README.md), [licencja](../../../assets/audio/LICENSE.md), [formaty i hashe](../../../assets/audio/manifest.json).

| Miejsce / zdarzenie | Dźwięk |
|---|---|
| Ulica | Deszcz, szum miasta i niski elektroniczny pomruk |
| Bar | Przytłumiony klubowy puls i ambient |
| Kryjówka | Wentylatory serwerów, szum elektroniki i ciche impulsy |
| Lobby | Klimatyzacja i spokojny elektroniczny akord |
| Rozmowa E | Krótki sygnał na rozpoczęcie rozmowy |
| Sklep | Osobny sygnał otwarcia i zamknięcia |
| Zakup | Potwierdzenie po faktycznie udanym zakupie |
| Kredyty | Sygnał jednorazowej wypłaty kontraktu |
| Walka | Zamach, trafienie i pokonanie szczura |
| Apteczka | Krótki sygnał regeneracji |
| Drzwi | Syntetyczny odgłos przejścia |

Nie dodano kroków, aby nie zagęszczać warstwy dźwiękowej.

## Implementacja

AudioManager opiera się na pygame.mixer. Cztery ambienty i efekty są wczytywane raz po odblokowaniu audio, a nie w pętli klatek. Jeden zarezerwowany kanał ambientu stosuje wygaszenie około 0,25 s i narastanie około 0,45 s. Nowa lokacja zastępuje poprzednią na tym samym kanale; ambienty nie nakładają się. Efekty mają osiem oddzielnych kanałów oraz krótki limiter powtórzeń.

Domyślny poziom kanału ambientu wynosi 0,22, efektów 0,32, przy dodatkowo umiarkowanej amplitudzie zapisanych próbek. Łącznie WAV-y zajmują około 1,53 MB. Format: mono, signed 16-bit PCM, 22050 Hz. Natywny mixer skonwertował je do swojego formatu 44100 Hz stereo; przeglądarkowy mixer poprawnie zdekodował wszystkie 14 plików.

Brak urządzenia lub błąd dekodowania nie przerywa gry. Nie ma ponawiania inicjalizacji co klatkę; błędny plik jest pomijany, a pozostałe mogą działać dalej. Dźwięki zdarzeń wywoływane są dopiero przy faktycznym zdarzeniu: nieudany zakup nie udaje potwierdzenia, a nieodebrany kontrakt nie wypłaca kredytów ani sygnału.

Mostek Web Audio odblokowuje konteksty SDL po zaufanym kliknięciu lub klawiszu. Test potwierdził uruchomienie po pierwszym Graj, bez drugiego kliknięcia i bez obchodzenia polityki autoplay. Audio działa lokalnie z plików dołączonych do archiwum gry, bez pobierania osobnych dźwięków podczas rozgrywki.

Pygbag 0.9.3 ma konserwatywną kontrolę formatów, która domyślnie odrzuca WAV i sugeruje OGG. Wybrano jawne pakowanie PCM WAV przez --disable-sound-format-error oraz --no_opt, bez automatycznego przepisywania plików przez ffmpeg. Poprawność tej decyzji potwierdziło rzeczywiste dekodowanie i pomiar wyjścia audio w Chrome — nie sam udany build.

## Sterowanie i brak zmian mechaniki

M włącza/wyłącza audio, także w sklepie i mapie. Wyciszenie pokazuje wyłącznie mały napis przy dole ekranu. W aktywnym polu tekstowym Buddy’ego litera M pozostaje wpisywanym tekstem. Wyciszenie jest zachowane przy R w tej samej karcie.

Nie zmieniano reguł walki, nagród, questów, sklepu, AI ani istniejących paneli. Dodano jedynie odtwarzanie efektów po odpowiednich zdarzeniach oraz dyskretny wskaźnik wyciszenia. Bez dźwięku rozgrywka pozostaje dostępna.

## Faktycznie wykonane testy

| Sprawdzenie | Wynik |
|---|---|
| Bazowy pytest przed zmianą | 274 zaliczone |
| Pełny pytest po dodaniu audio | **284 zaliczone**, jedno istniejące ostrzeżenie deprecacyjne narzędzia testowego |
| Testy nowej logiki audio | Gest, brak duplikacji, jeden ambient, przejścia, M, błędne urządzenie/dekoder, efekty sukcesu i ochrona ambientu przed efektami |
| Natywny Pygame / rzeczywisty domyślny mixer | 60 wyrenderowanych klatek, około **60,25 FPS**, 14 dźwięków, działający ambient i efekt |
| Natywny brak urządzenia | Celowo nieistniejący sterownik: 12 klatek, gra działa, audio bezpiecznie niedostępne |
| Docker / pygbag | Build zakończony sukcesem, kontenery uruchomione |
| Chrome po Graj | 14 załadowanych WAV, aktywny AudioContext, niezerowy zmierzony sygnał PCM |
| Chrome M | Zmierzona cisza RMS=0; ponowne M przywróciło sygnał |
| Przejścia ulica → bar → ulica | Prawidłowe pojedyncze uruchomienia ambientów, jeden kanał i jeden węzeł wyjściowy |
| Pozostałe lokacje | Kryjówka i lobby z właściwymi ambientami i powrotem na ulicę |
| Rozgrywka | Barman, sklep otwarcie/zamknięcie, 3 pokonane szczury, 6 trafień, apteczka, wypłata 36 KR i zakup ulepszenia broni |
| Błędy podczas przebiegu | 0 błędów API/JS i 0 błędów dekodowania audio |

[Pełny pytest](evidence/pytest.txt), [test bazowy](evidence/pytest-baseline.txt), [build](evidence/build.txt), [natywny mixer i FPS](evidence/native-audio.json), [brak urządzenia](evidence/native-no-device.json), [zrzut natywny](evidence/native-audio.png).

### Pomiar przeglądarkowy i wydajność

Test obserwował rzeczywisty węzeł wyjściowy Web Audio, nie tylko flagę „odtwarzam”. Przed kliknięciem nie było dźwięku. Dla ulicy RMS wynosił około 0,022–0,025; bar około 0,005–0,006, kryjówka około 0,010, lobby około 0,005. Przy M wynik wynosił dokładnie 0. Wszystkie 14 punktów kontroli audio w przebiegu rozgrywki zostały wykonane: [wyniki przebiegu](evidence/browser-audio-progress.json).

Pierwszy skrypt zakończył się błędem dopiero na założeniu, że odświeżanie testowego Chrome musi przekraczać 45 Hz; funkcjonalne sprawdzenia audio i rozgrywki już wtedy się powiodły. Nie przedstawiamy tego skryptu jako zakończonego bez błędu.

Osobny, prawidłowy test porównawczy zakończył się sukcesem: przed grą około 26,49 Hz, audio włączone 29,99 Hz, wyciszone 28,51 Hz, przywrócone 29,99 Hz. Nie zaobserwowano regresji związanej z audio. To pomiar odświeżania requestAnimationFrame w testowym Chrome, a nie deklaracja 60 FPS silnika na każdym komputerze. Natywne renderowanie faktycznie osiągnęło około 60 FPS.

[Pomiar porównawczy](evidence/browser-audio-performance.json), [nagranie rzeczywistego wyjścia audio](evidence/browser-live-audio.webm), [sklep po walce](evidence/browser-audio-shop.png), [wyciszenie](evidence/browser-muted.png).

## Późniejsze polecenie: wszystkie integracje META

Pierwotnie etap audio zakładał brak płatnych wywołań. Użytkownik następnie wyraźnie zmienił polecenie: wyłączyć mocki i testować z prawdziwym LLM, także płatnie. Zgodnie z tym:

- BUDDY_MODE=meta i META_ALLOW_PAID_REQUESTS=true.
- DIRECTOR_MODE=meta i DIRECTOR_ALLOW_PAID_REQUESTS=true.
- WORLD_AI_MODE=meta i WORLD_AI_ALLOW_PAID_REQUESTS=true.
- Na osobno wybraną przez użytkownika wartość ustawiono WORLD_AI_GLOBAL_LIMIT=50. Nie zerowano licznika; przy zmianie zapisane było 12 wykorzystanych prób. Limit sesji 6, cooldown 30 s, maksymalna odpowiedź 2400 tokenów i budżet 150000 tokenów pozostały zachowane.
- ASSET_AI_MODE=meta, ale nowe generacje obrazów pozostają wyłączone (ASSET_AI_ALLOW_PAID_REQUESTS=false). Istniejące obrazy Meta pochodzą z cache. Nie generowano żadnego obrazu ani płatnego dźwięku.

Znaleziony wpis ASSET_AI_GLOBAL_LIMIT=8 blokował start backendu, ponieważ istniejący rejestr obsługuje 3 identyfikatory. Przywrócono zgodną wartość 3. Nie dotyczy to liczby wywołań LLM.

Działające API po restarcie potwierdziło trzy tryby LLM jako meta, a oba kontenery były zdrowe. Główny przebieg audio zarejestrował dwie rzeczywiste odpowiedzi World META (bez podstawiania odpowiedzi mock). W tym przebiegu nie wysyłano dodatkowych wiadomości Buddy’emu ani nie kończono pierwszego questu, więc nie wywoływano dodatkowo ich płatnych generacji. Krótki test wydajności korzystał z tej samej aktywnej konfiguracji META. Pozostałej równoległej aktywności użytkownika nie przypisujemy kosztom testu audio. Liczników nie modyfikowano ręcznie.

## Uruchomienie

Gra jest uruchomiona pod http://localhost:8080. Otwórz świeżą kartę lub Ctrl+F5, kliknij Graj, następnie użyj M do wyciszenia/włączenia. Admin: http://localhost:8080/admin. Standardowy ponowny start: docker compose up --build -d.

W grze sprawdź F do baru, E przy Barmanie, E przy Nyx, Esc ze sklepu, Spację przy szczurze i H po otrzymaniu obrażeń. Audio odtwarza tylko zdarzenia, które naprawdę nastąpiły.

## Ograniczenia i następny krok

Nie przeprowadzono odsłuchu na fizycznych głośnikach użytkownika ani testu mobilnego Safari. Potwierdzono natywny mixer Windows i rzeczywisty sygnał wyjściowy w desktopowym Chrome. Domyślna głośność jest celowo umiarkowana. Ambienty są krótkimi syntetycznymi pętlami, nie pełnym soundtrackiem. Nie ma kroków ani voice-overu.

Dalszych testów nie uruchamiano po poleceniu użytkownika „już nie testuj”. Następny krok: użytkownik nagrywa przygotowaną grę i ustawia poziom głośności systemu odpowiednio do filmu. Nie wykonano commita.
