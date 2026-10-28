# Zadanie dla Codexa — wykonaj POC 01

Przeczytaj `AGENTS.md`, `docs/POC_SPEC.md` oraz sprawdź wszystkie dostępne pliki w katalogu **`grafika/`** (w tym podfoldery). To są oryginalne grafiki mojej gry Chess Corp. **Zainspiruj się nimi i wykorzystaj je tam, gdzie pasują, ale samodzielnie zbuduj kompletny grywalny POC.** Nie czekaj na dodatkowe grafiki.

## Przebieg pracy
1. Zrób inwentaryzację `grafika/` i ustal, które pliki nadają się na tło, sprite gracza, Buddy'ego i UI. Zapisz wynik w `docs/ASSET_REPORT.md`.
2. Utwórz projekt Python z `uv`, `pygame-ce`, `pytest` i minimalną strukturą plików.
3. Wyświetl jedną scenę ulicy w stylistyce przesłanych grafik. Dopasuj skalę i pas ruchu postaci.
4. Dodaj gracza i ruch WASD, ograniczenie sceny, podstawową animację (jeśli realnie dostępna).
5. Dodaj Buddy'ego, promień interakcji i podpowiedź `[E] Rozmawiaj`.
6. Dodaj okno dialogowe i HUD questu.
7. Wczytaj scenę, dialogi i quest z JSON. Zaimplementuj trzyetapowy quest opisany w specyfikacji.
8. Dodaj testy: wczytanie JSON, kolejność etapów questu, interakcja tylko w zasięgu, brak podwójnej nagrody.
9. Uruchom testy, napraw błędy, wykonaj smoke test Pygame.
10. Spróbuj uruchomić wersję przez pygbag; zapisz dokładne komendy i wynik w README.

## Krytyczne zasady
- Nie kończ na planie. **Masz napisać działający kod i go uruchomić.**
- Nie dodawaj teraz AI, FastAPI, Dockera, bazy danych, generowania grafik ani nowych mechanik.
- Nie nadpisuj `grafika/` i nie usuwaj żadnych oryginałów.
- Nie wywołuj płatnych API.
- Gdy napotkasz problem, diagnozuj i naprawiaj go; zadawaj pytania tylko przy rzeczywistym blokerze.
- Gdy nie możesz przeprowadzić wizualnego testu, powiedz to wprost.

## Warunek zakończenia
Gra uruchamia się lokalnie, gracz chodzi WASD, rozmawia z Buddy'm po E, odbiera identyfikator przy wejściu i kończy quest po powrocie. Testy przechodzą. Dostaję po polsku krótki raport i instrukcję uruchomienia.
