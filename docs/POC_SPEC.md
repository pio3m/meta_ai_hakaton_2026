# Chess Corp — POC 01: Pierwszy dzień w korporacji

## Cel
Jedna grywalna, krótka scena wykorzystująca oryginalne grafiki Chess Corp. Ma pokazać **ruch → interakcję → dialog → zmianę celu → ukończenie questu**. Bez integracji AI w tej iteracji, ale zawartość definiowana przez JSON, aby w następnej iteracji AI mogło ją generować.

## Kierunek artystyczny
Dostarczone materiały przedstawiają mroczną neonową ulicę, granatowo-turkusową paletę, postać w kapturze i interfejs pixel-art. Zachowaj klimat oryginału. Preferuj nearest-neighbor scaling, brak wygładzania i spójną skalę postaci. Nie wstawiaj stockowych grafik, jeśli zasoby użytkownika wystarczą.

## Kamera i sterowanie
- **Side-view / 2.5D beat'em up**, nie top-down: tło ulicy jest widziane z boku.
- `A/D`: lewo/prawo; `W/S`: niewielka zmiana głębi na pasie chodnika.
- `E`: interakcja z najbliższym aktywnym obiektem w promieniu, z priorytetem zależnym od etapu questu.
- `Esc`: zamknięcie dialogu; w dialogu `E` lub `Enter`: kolejna wypowiedź / zamknięcie.
- Brak skoku, walki, fizyki i rozbudowanej kamery w POC.
- Dostosuj prędkość ruchu do delta time. Nie pozwalaj przechodzić poza scenę lub przez zablokowane obszary.

## Quest: Pierwszy dzień
1. **Porozmawiaj z Buddy'm** — Buddy wita gracza i poleca odebrać identyfikator przy wejściu Chess Corp.
2. **Odbierz identyfikator** — gracz podchodzi do właściwych drzwi/terminala, wciska `E`; pojawia się komunikat, że otrzymał identyfikator.
3. **Wróć do Buddy'ego** — Buddy gratuluje; quest oznaczony jako ukończony.

Nie można odebrać identyfikatora przed rozmową z Buddy'm ani zaliczyć questu bez identyfikatora. Powtarzanie `E` nie powinno dublować nagrody.

## Zasoby
Zajrzyj do `grafika/`. Przykładowe nazwy występujące w materiałach użytkownika (nie zakładaj, że są identyczne w repozytorium):
- `Dude_white.png`, `Dude_white(1).png` — prawdopodobny spritesheet ruchu; zbadaj układ klatek, duplikaty i kolor tła.
- `Dude2.png` — osobny sprite postaci.
- `Tło.png`, `Tło(1).png` — uliczne tło, warianty z szyldami.
- `Building1_base.png`, `Building1_blue.png`, `Building1_green_neon1.png` — elementy budynku.
- `Screen_base.png`, `Screen_progress.png` — inspiracja dla UI; mogą nie być gotowymi komponentami.
- `Combat_arena.gif`, `Defeat_wip.gif` — **nie są potrzebne w POC**.

Uwaga: jeśli postać ma tylko animacje skierowane w jedną stronę, można użyć flip poziomego dla ruchu w lewo. Jeżeli arkusz nie zawiera odpowiednich klatek, wystarczy animacja 2–4 klatek lub nawet statyczna postać z poprawnym ruchem. **Najważniejsza jest grywalność.**

## Minimalne moduły
- `main.py` — start gry, pętla zdarzeń.
- `game/world.py` — scena, ograniczenia ruchu, obiekty.
- `game/player.py` — ruch i sprite.
- `game/interactions.py` — promień interakcji, E.
- `game/quests.py` — prosty automat stanów na podstawie JSON.
- `game/ui.py` — HUD, dialog, podpowiedzi.
- `content/scene.json`, `content/quest_first_day.json`, `content/dialogues.json`.
- `tests/` — testy logiki niezależne od renderowania.

Struktura jest wskazówką, nie obowiązkową abstrakcją. Nie buduj frameworka.

## Przeglądarka
Pętla asynchroniczna, brak blokujących wywołań. Sprawdź zgodność pygbag możliwie wcześnie. Nie deklaruj sukcesu bez rzeczywistego testu.

## Akceptacja manualna
- Uruchamiam grę i widzę ulicę z grafik użytkownika.
- Chodzę `WASD`; sprite nie rozmywa się przy skalowaniu.
- Przy Buddy'm widzę podpowiedź `E` i mogę rozpocząć dialog.
- HUD pokazuje kolejny cel.
- Przy właściwych drzwiach odbieram identyfikator.
- Po powrocie do Buddy'ego quest kończy się.
- Gra nie wywala się po szybkim wciskaniu `E`, opuszczeniu zasięgu lub ponownej rozmowie.
