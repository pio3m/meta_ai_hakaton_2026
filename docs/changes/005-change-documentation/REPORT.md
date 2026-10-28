# Organizacja dokumentacji zmian — raport

Data zmiany: 28.10.2026.

## Cel i zakres

Każda duża zmiana ma własny opis zakresu i raport weryfikacji. Dokumentacja historyczna została uporządkowana przez indeks i karty etapów, bez przenoszenia wcześniejszych plików.

## Zmienione miejsca

- `AGENTS.md`: trwałe instrukcje dla kolejnych zmian.
- `docs/README.md`: indeks dokumentacji.
- `docs/changes/README.md`: rejestr etapów i konwencja.
- `docs/changes/_template/`: szablony changelogu i raportu.
- `docs/changes/001-poc01/` do `005-change-documentation/`: karty zmian.
- `README.md`: odnośnik do indeksu dokumentacji.

## Weryfikacja

Sprawdzono istnienie plików, względne linki Markdown w nowej dokumentacji i poprawność diffu. Kod gry nie został zmieniony; testów gry nie uruchamiano ponownie dla tej zmiany dokumentacyjnej. Nie wykonano żadnych wywołań Meta.

## Ograniczenia i następny krok

Karty historyczne podsumowują wcześniejsze raporty, a nie nowe testy. Przy kolejnej dużej zmianie skopiuj szablon do katalogu `006-<slug>` i dodaj wpis w indeksie zmian.
