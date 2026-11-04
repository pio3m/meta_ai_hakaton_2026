# Zatrzymywanie NPC do rozmowy — raport

Data: 2026-11-04.

## Zachowanie

Podejście do dowolnego NPC na 65 pikseli zatrzymuje go i odwraca w kierunku gracza. Postać wita gracza; E wyświetla kolejną kwestię. Panel pozostaje widoczny, gdy gracz stoi obok. Po odejściu na ponad 100 pikseli postać wznawia przerwany ruch. Dwa promienie zapobiegają ciągłemu ruszaniu i zatrzymywaniu na granicy rozmowy.

Przerwana akcja nie kończy się przez upływ czasu rozmowy. Zatrzymanie jest lokalną mechaniką, nie nowym wywołaniem LLM. Dla Security, Hackera i Employee rozmowa składa się z krótkich, cyklicznych kwestii mock; nie dodano swobodnego chatu tekstowego dla tych postaci. Buddy zachowuje istniejący swobodny chat, Guard i priorytet pierwszego questu. Questy i terminale nadal mają pierwszeństwo przy E, jeśli gracz stoi w ich zasięgu.

## Testy

- Pełny pytest: **238 passed**, 1 znane ostrzeżenie Starlette/httpx, 20,98 s.
- Pięć nowych przypadków obejmuje zatrzymanie, kierunek spojrzenia, wstrzymanie czasu i wznowienie dla każdego z czterech NPC oraz wybór najbliższej postaci i zmianę kwestii po E.
- Testy wykonania planów bez interakcji gracza pozostają osobno sprawdzane; scenariusz sześciu akcji nie umieszcza już gracza tuż przy wykonującym je NPC.
- Lokalny Pygame: 12 wyrenderowanych klatek. Docker/pygbag zbudowane i uruchomione na 8080.
- Przeglądarka: potwierdzono powitanie i zatrzymanie Security, kolejną odpowiedź po E, wznowienie ruchu po odejściu i zatrzymanie Buddy’ego. Pierwszy quest ukończono klawiaturą. Dowody: `evidence/npc-conversation.png`, `evidence/npc-resume-buddy-stop.png` oraz `evidence/first-quest-completed.png`.
- Wszystkie płatne zgody pozostają wyłączone; nie wykonano płatnych wywołań.

## Użycie

Otwórz nową kartę http://localhost:8080 i kliknij Graj. Podejdź blisko postaci; zatrzyma się i przywita. E: następna kwestia (Buddy: dotychczasowa rozmowa / quest). Odejdź, aby postać wróciła do swoich zajęć.

## Ograniczenia

Jeśli kilka NPC jest blisko, zatrzyma się każdy w zasięgu; E wybiera najbliższego, a jeden panel rozmowy zachowuje czytelność UI. Swobodny chat tekstowy nadal dotyczy Buddy’ego.
