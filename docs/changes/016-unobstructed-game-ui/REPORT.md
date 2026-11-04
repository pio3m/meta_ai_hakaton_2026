# Raport 016 — odsłonięta scena gry

Data: 2026-11-04. Status: zakończone i sprawdzone.

## Zmiana

Z gry usunięto stałą listę NPC ze stanami „Patroluje”, „Obserwuje”, „Bada terminal” i źródłami META/MOCK/FALLBACK. Nie ma już dodatkowego paska „Żyjąca ulica”. Te informacje znajdują się teraz w osobnych, czytelnych kartach NPC na stronie /admin i w ograniczonym do jego sesji widoku jury. Karty automatycznie odświeżają stan, cel, nastrój, pozycję, źródło zachowania i dwa ostatnie wspomnienia. Wykorzystują istniejącą telemetrię; nie wysyłają zapytań do LLM.

Automatyczne przywitanie pobliskiego NPC nie otwiera dużego panelu. Przy postaci pojawia się mała podpowiedź E; dopiero jawna rozmowa otwiera panel z tekstem. Questy Buddy’ego i okno czatu działają nadal. HP, kredyty i apteczki mieszczą się w głównym nagłówku. Zmniejszono panel dodatkowego questu i usunięto stały baner gratulacyjny, bo ukończenie jest już widoczne w celu zadania.

Zachowano oryginalne grafiki, cztery lokacje, sterowanie, walkę, sklep, questy i konfigurację kosztów. Nie zmieniano zachowań AI ani walidacji. Pełne prompty pozostają w zabezpieczonym Inspectorze, a jury ma nadal dostęp tylko do wydzielonej sesji.

## Weryfikacja

- `python -m pytest -q`: **274 zaliczone**, jedno istniejące ostrzeżenie deprecacyjne biblioteki testowej. [Log](evidence/pytest.txt).
- Natywny Pygame: **12 klatek bez błędu**, z wyłączoną siecią. [Zrzut](evidence/native-clear-ui.png).
- Docker Compose / pygbag: build zaliczony. [Log](evidence/build.txt).
- Test Chrome wykonywany klawiaturą w tymczasowym trybie mock: odsłonięta ulica, ukończony pierwszy quest, kompaktowy panel Directora, rozmowa E z Barmanem i nowy podgląd NPC w adminie. **Wynik: zaliczone, 0 błędów API/JS.** [Przebieg](evidence/browser-results.json), [czysta ulica](evidence/browser-clear-street.png), [mały panel questu](evidence/browser-compact-quest.png), [rozmowa Barmana](evidence/browser-explicit-barman.png), [karty NPC w adminie](evidence/admin-npc-status-cards.png).

Nowe grafiki nie były generowane. Weryfikacja UI nie wykonuje płatnych wywołań. Domyślnej konfiguracji użytkownika w .env nie zmieniano; mock był tylko tymczasowym ustawieniem kontenerów na czas testu.

## Uruchomienie

Gra nadal działa na http://localhost:8080, panel na http://localhost:8080/admin. Po aktualizacji otwórz świeżą kartę gry lub naciśnij Ctrl+F5. Admin także odśwież; po restarcie backendu może wymagać ponownego zalogowania istniejącym tokenem właściciela. Standardowy start: `docker compose up --build -d`.

Rozmowę otwieraj E przy NPC. Statusy autonomicznych postaci oglądaj w adminie w sekcji „Świat na żywo”. W normalnej grze nie trzeba utrzymywać otwartego panelu diagnostycznego.

## Ograniczenia i następny krok

Okna czatu, sklepu, mapy i zagadki nadal świadomie zajmują większą część ekranu po ich otwarciu przez gracza. Aktywny quest ma mały panel z celem, aby zachować czytelne wskazówki. Następny krok: odświeżyć oba okna prezentacji i korzystać z admina do obserwowania NPC.

Licznik World AI pozostał identyczny przed i po sprawdzeniu: 7 prób i 20265 tokenów (obejmuje wcześniejsze użycie użytkownika). Ta zmiana i jej testy nie dodały płatnych wywołań. Po zamknięciu przeglądarki testowej przywrócono konfigurację META z istniejącego .env, bez resetowania budżetu.
