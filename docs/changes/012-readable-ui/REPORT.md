# Czytelny interfejs i wyłącznie mock — raport

Data: 2026-11-04.

## Zakres

Uproszczono UI Living AI World bez zmiany mechaniki, grafik, questów i logiki NPC. Jeden panel wypowiedzi zastępuje cztery dymki z liniami; lista postaci ma stałe położenie i polskie opisy czynności. Usunięto diagnostykę znad postaci i z dziennika ekranowego. Szczegóły nadal są w /admin. Pierwszy quest, dynamiczne questy, rozmowa Buddy’ego i Guard pozostają aktywne.

W konfiguracji uruchomionego backendu potwierdzono: BUDDY_MODE=mock, DIRECTOR_MODE=mock, WORLD_AI_MODE=mock oraz META_ALLOW_PAID_REQUESTS=false, DIRECTOR_ALLOW_PAID_REQUESTS=false, WORLD_AI_ALLOW_PAID_REQUESTS=false. W tym etapie nie wykonano płatnych wywołań. Lokalny .env pozostaje ignorowany przez Git; klucze nie trafiły do dokumentacji.

## Weryfikacja

- Pełny istniejący zestaw pytest: **233 passed**, 1 znane ostrzeżenie Starlette/httpx; 21,33 s.
- Lokalny start Pygame, SDL dummy: 12 wyrenderowanych klatek; dowód evidence/pygame-smoke.png.
- Budowa Docker/pygbag: zakończona powodzeniem. Backend i gra uruchomione na localhost:8080.
- W przeglądarce ukończono pierwszy quest (Buddy → identyfikator → Buddy), po czym uruchomił się dynamiczny COLLECT w mocku. Panel zadania i wypowiedź NPC zajmują osobne miejsca.
- Sprawdzono nowy układ w przeglądarce. Wypowiedzi i lista czynności zajmują osobne, stałe miejsca i nie zasłaniają NPC.

Dowody przeglądarkowe: `evidence/readable-ui.png` oraz `evidence/quest-ui.png`.

## Użycie

Otwórz nową kartę http://localhost:8080 i kliknij Graj. Jeśli korzystasz ze starej otwartej gry, zamknij ją i otwórz ponownie, aby pobrać nową paczkę. Sterowanie bez zmian. F4: wybór scenariusza demo. Przy kolejnym uruchomieniu wystarczy `docker compose up --build -d`.

## Ograniczenia

W danej chwili wyświetlana jest jedna wypowiedź otoczenia, aby była czytelna. Pełna diagnostyka świata pozostaje w Inspectorze. Dłuższe wypowiedzi mają limit trzech wierszy (dwóch podczas dynamicznego questu). Model, postacie i mechaniki pozostają bez zmian.
