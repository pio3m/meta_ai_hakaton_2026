# Raport 022 — uporządkowanie README dla GitHuba

## Zakres

Główny README jest w całości po angielsku i prezentuje aktualny zakres gry. Rozdziela trzy integracje Muse Spark, generowanie obrazów Muse Image i lokalne reguły wykonania. Wskazuje uczciwie, że rat bounty contracts są gotowymi scenariuszami, a zadania Directora i dwie misje sesji są odrębnymi ścieżkami generacji. Tłumaczy również różnicę między otwarciem dziennika J i utworzeniem nowej sesji oraz ponownym użyciem sesji demonstracyjnej.

Archiwum zawiera całą poprzednią treść README, poprzedzoną informacją o historycznym charakterze opisów. Odnośniki względne przeliczono względem docs/. Nie usuwano raportów, dowodów testów ani wcześniejszej dokumentacji.

## Faktycznie wykonane sprawdzenia

- Przeczytano ustawienia przykładowe, kod adapterów, generowania obrazów, Inspectora i sterowania; nie zmieniano tych plików.
- Sprawdzono 26 względnych odnośników głównego README i archiwum: brak nieistniejących celów.
- Sprawdzono kompletność bloków kodu, odnośniki wewnętrzne i język tekstu głównego.
- README wyrenderowano przez rzeczywisty GitHub Markdown API w trybie GFM z kontekstem publicznego repozytorium. W Chrome potwierdzono nagłówek, trzy tabele, załadowany screenshot gry i brak poziomego przepełnienia dokumentu. Zrzut: evidence/github-markdown-preview.png. Podgląd używa HTML zwróconego przez GitHuba i lokalnych stylów do kontroli układu.
- Porównanie sum kontrolnych plików kodu, konfiguracji i zapisów kosztów w chwili audytu: bez zmian. Wynik: evidence/checks.json.
- Przed publikacją sprawdzono dodawane pliki pod kątem rzeczywistych sekretów z lokalnego .env i wzorców tokenów; nie dodano kluczy, haseł, tokenów, prywatnych promptów ani lokalnych liczników.

Nie uruchamiano pytest ani rozgrywki: zmiana obejmuje wyłącznie dokumentację. Nie wykonano płatnych wywołań Meta i nie restartowano kontenerów. Końcowa kontrola opublikowanej strony GitHub i zgodności zdalnego commita jest podawana w odpowiedzi po push.

## Zmienione pliki

- README.md.
- docs/DEVELOPMENT_HISTORY_PL.md.
- docs/changes/README.md — indeks zmian.
- docs/changes/022-readme-cleanup/CHANGELOG.md i REPORT.md.
- docs/changes/022-readme-cleanup/evidence/checks.json i github-markdown-preview.png.

## Ograniczenia

Link do filmu YouTube pozostaje jawnym miejscem do uzupełnienia. Dokumentacja historyczna pozostaje po polsku, zgodnie ze zleceniem. Nie nadano nowych licencji grafikom ani całemu repozytorium. Następny krok: dopisanie rzeczywistego linku do filmu po jego opublikowaniu.
