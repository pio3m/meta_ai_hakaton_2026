# POC 03 — AI Game Director

Data: 2026-10-28. Status: zakończona implementacja i testy mock; prawdziwe wywołanie Directora wymaga osobnej zgody.

## Dodano

- `POST /api/director`, korzystający ze wspólnego adaptera HTTP Muse Spark i rejestratora AI Inspector.
- Ścisły schemat Pydantic `DirectorPlan`: tylko `create_quest` i `place_object`, jeden nośnik danych i warunek `collect_object`.
- Reguły sceny w `content/director_rules.json`: dwa zatwierdzone miejsca, stałe identyfikatory i zasięg interakcji.
- Walidację schematu, referencji, dozwolonych działań, długości tekstów, obszaru ruchu, kolizji i dostępności miejsca; dodatkową walidację w Pygame przed atomowym zastosowaniem planu.
- Automatyczny start jednego zadania po ukończeniu pierwszego dnia, obiekt na ulicy, HUD oraz deterministyczne ukończenie przez E. G ponawia tylko nieudaną generację; R rozpoczyna nową sesję.
- Oddzielny mock Directora i osobną blokadę płatnych wywołań. Sukces i błędy są pamiętane w sesji; brak automatycznych ponowień API.
- Inspector: typ Buddy/Director, odpowiedź JSON, wynik walidacji i zatwierdzony plan w ograniczonym widoku jury.
- Kontekst zadania Directora przekazywany Buddy’emu; wspólny transport przeglądarkowy obsługuje dwa jawnie dozwolone endpointy.
- 25 dodatkowych testów; raport i dowody pełnego przejścia scenariusza w przeglądarce.

## Zachowano

Oryginalne grafiki, pierwszy quest i nagrodę, ruch gracza, rozmowę z Buddy’m, zabezpieczenia panelu, limit 200 wpisów RAM i port 8080. Nie dodano Guarda, spacerowania NPC, audio, Langfuse ani bazy danych. Nie wykonano nowego płatnego wywołania Meta.
