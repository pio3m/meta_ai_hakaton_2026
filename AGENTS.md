# Chess Corp — stałe instrukcje dla Codexa

## Misja
Jesteś głównym programistą gry Chess Corp. Twoim celem jest **jak najszybsze dostarczenie grywalnego POC**, a nie budowanie produkcyjnej platformy. Pracuj autonomicznie w zakresie zadania: **analiza → implementacja → test → naprawa → ponowny test**. Nie kończ na napisaniu kodu ani na samym planie.

## Zasoby — obowiązkowo
- **Oryginalne grafiki użytkownika znajdują się w katalogu `grafika/` w głównym katalogu repozytorium.** Katalog może zawierać podfoldery.
- Najpierw wykonaj inwentaryzację plików w `grafika/` (nazwy, rozdzielczości, formaty, przezroczystość, arkusze animacji), potem dobierz sposób użycia.
- **Nie zakładaj**, że wszystkie klatki spritesheetu mają poprawne wymiary, że tło jest tilemapą ani że czarne tło oznacza przezroczystość. Sprawdź rzeczywiste dane.
- Możesz korzystać z grafik jako referencji stylu, wycinać kadry i przygotowywać pochodne pliki w `assets/processed/`; **nie nadpisuj oryginałów w `grafika/`**.
- Jeśli konkretna grafika nie nadaje się do użycia, zastosuj prosty placeholder w zgodnej palecie. Nie blokuj ukończenia POC.
- Nie generuj nowych obrazów przez płatne API bez zgody użytkownika.

## Stos technologiczny
- Python 3.12+, `uv`, `pygame-ce`, `pytest`.
- Docelowo przeglądarka przez `pygbag`; **w pierwszym POC nie dodawaj FastAPI, AI, bazy, Docker Compose ani Azure**.
- Użyj asynchronicznej pętli gry zgodnej z pygbag (`async def main`, `await asyncio.sleep(0)` w każdej klatce).
- Gra lokalna ma działać bez Internetu. Ścieżki do zasobów buduj względem lokalizacji projektu, nie bieżącego katalogu procesu.

## Język
- Raporty i instrukcje dla użytkownika po polsku.
- Nazwy klas, funkcji, zmiennych, plików kodu i kluczy JSON po angielsku.
- Teksty gry w pierwszym POC po polsku, z możliwością późniejszej lokalizacji.

## Zakres POC
Jedna scena ulicy w stylu dostarczonych grafik (perspektywa **side-view z ograniczonym pasem głębi**), gracz poruszany WASD, Buddy, interakcja E, dialog, jeden krótki quest i czytelne UI. Szczegóły: `docs/POC_SPEC.md`.

## Jak pracować
1. Sprawdź repozytorium i katalog `grafika/`.
2. Krótko zapisz plan i zacznij implementację bez czekania na kolejne potwierdzenie.
3. Realizuj najmniejszą działającą wersję. Unikaj ECS, systemu pluginów, abstrakcyjnego silnika, skomplikowanego edytora.
4. Dane sceny, dialogów i questu trzymaj w JSON; nie wykonuj kodu z JSON.
5. Dodaj testy logiki questu, interakcji i wczytywania danych.
6. Uruchom testy i napraw błędy. Uruchom również test startu gry (np. SDL_VIDEODRIVER=dummy) i sprawdź, czy wykonuje kilka klatek.
7. Spróbuj uruchomić / zbudować wersję przez pygbag. Jeśli nie możesz wizualnie sprawdzić przeglądarki, napisz to wprost — nie udawaj weryfikacji.
8. Zostaw działający projekt, README i proste komendy uruchomienia.

## Bezpieczeństwo i ograniczenia
- Nie usuwaj cudzych plików, nie nadpisuj `grafika/`, nie rób commitów bez prośby.
- Nie korzystaj z płatnych usług ani nie wdrażaj niczego na Azure bez zgody.
- Jeśli grafiki mają niejasne licencje, zachowaj je wyłącznie jako zasoby użytkownika; nie deklaruj ich jako open source.
- Nie zmieniaj silnika na Godot/Phaser.

## Definicja ukończenia
- Pygame startuje lokalnie.
- Widać scenę ulicy inspirowaną grafikami użytkownika.
- Gracz chodzi WASD i nie wychodzi poza obszar ruchu.
- W pobliżu Buddy'ego pojawia się podpowiedź `[E] Rozmawiaj`.
- E uruchamia dialog i aktualizuje quest.
- Gracz wchodzi w interakcję z właściwymi drzwiami, odbiera identyfikator i wraca do Buddy'ego.
- Quest kończy się czytelnym komunikatem.
- Testy przechodzą; ograniczenia pygbag są opisane.

## Raport końcowy
Po polsku: (1) zrobione, (2) wykorzystane grafiki i sposób cięcia, (3) komendy testów i wyniki, (4) uruchomienie lokalne i status pygbag, (5) ograniczenia, (6) następny najmniejszy krok. Nie twierdź, że coś zostało sprawdzone, jeśli nie było.
