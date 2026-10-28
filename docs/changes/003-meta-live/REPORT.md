# Pierwsze prawdziwe wywołanie Muse Spark — raport

Data zmiany: 28.10.2026.

Karta odtworzona 28.10.2026 na podstawie wcześniejszej dokumentacji i historii Git.

## Cel i zakres

Zweryfikowanie połączenia z prawdziwym Meta API po uzyskaniu zgody użytkownika. Klucza i jego wartości nie zapisujemy w dokumentacji.

## Weryfikacja historyczna

- Jedno prawdziwe wywołanie: HTTP 200, provider `meta`, odpowiedź po polsku.
- Czas odpowiedzi: 2,31 s; historia zawierała dwie wiadomości.
- Po doprecyzowaniu promptu: 38 testów przeszło.
- Nie wykonywano drugiego płatnego zapytania do sprawdzenia poprawki promptu.

## Materiały

- [Raport z sekcją pierwszego testu prawdziwego API](../../POC02_REPORT.md)

## Ograniczenia

Połączenie działało, ale model może wymyślać szczegóły. Zmiana instrukcji została sprawdzona testem, nie kolejnym płatnym wywołaniem. To zapis historyczny; utworzenie tej karty nie wiązało się z nowym zapytaniem do Meta.
