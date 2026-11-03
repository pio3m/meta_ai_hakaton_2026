# Włączenie trybu Meta po zmianie konfiguracji

Data: 2026-11-02.

## Changelog

Użytkownik włączył zgodę na płatne wywołania, ale w lokalnym `.env` brakowało `DIRECTOR_MODE`. Compose i backend wybierały domyślne `mock`. Dopisano `DIRECTOR_MODE=meta`, zachowując istniejące zgody użytkownika, i odtworzono istniejące kontenery bez budowy. Nie zmieniano kodu ani sekretów.

## Sprawdzenie

Przed poprawką odczytano plik, wynik Compose i konfigurację kontenera: wszystkie wskazywały brak ustawienia lub tryb mock. Po poprawce sprawdzono `Settings.from_env()` wewnątrz kontenera i stan usług. Nie wykonano żądania generacji ani rozmowy z Buddy’m.

Nowy tryb dotyczy nowej generacji. Już wygenerowany quest mock w otwartej grze nie zmienia się po restarcie backendu: potrzebna jest nowa sesja R i ponowne ukończenie pierwszego questu. Opis „scenariusz mock” przy F4 przed generacją oznacza selektor testowy; dopiero odpowiedź serwera ustawia dostawcę META lub MOCK na HUD zadania.

Ustawienia Meta są teraz aktywne zgodnie z intencją użytkownika. Samodzielne ukończenie pierwszego questu w nowej sesji może wywołać płatną generację. Historyczny wynik testu i wyłączenia zgody w REPORT.md pozostaje zapisem poprzedniego testu, nie opisem bieżącej konfiguracji po tej zmianie.
