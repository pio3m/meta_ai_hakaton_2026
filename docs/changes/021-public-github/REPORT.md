# Raport 021 — publikacja GitHub

Użytkownik wskazał https://github.com/pio3m/meta_ai_hakaton_2026.git i polecił wypchnąć main. Repozytorium sprawdzono przez GitHub CLI: PUBLIC, przed publikacją puste, właściciel pio3m. Zachowano historię lokalnych commitów.

Przed wysyłką przeskanowano 964 historyczne bloby Git oraz bieżące pliki pod kątem wartości kluczy i tokenów z lokalnego .env oraz wzorców tokenów GitHub. Nie znaleziono dopasowań; nie znaleziono plików przekraczających 95 MB. Plik .env nigdy nie występował w historii sprawdzanego repozytorium. Ignorowane pozostają prywatne metadane assetów, liczniki kosztów, środowisko Python i buildy.

README otrzymał angielskie wprowadzenie, sterowanie i bezpieczny start w mocku. Oryginalnych grafik użytkownika nie zadeklarowano jako open source. Aktualne assety Meta zachowują publiczne metadane pochodzenia. Dołączono wcześniejszą poprawkę głośności ulicy.

Testy historyczne ostatniej wersji: pełny pytest 308 passed; po wyciszeniu deszczu 10 testów audio passed oraz kontrola głośności ulicy, baru i efektów. Podczas samej publikacji tych testów nie uruchamiano ponownie i nie wykonywano płatnych wywołań Meta. Konfiguracji działającego demo i liczników nie zmieniano. Polecenia publikacji: git remote add origin, git branch -M main, git push -u origin main. Status zdalnej gałęzi i lokalnej sprawdzany po wysłaniu.
