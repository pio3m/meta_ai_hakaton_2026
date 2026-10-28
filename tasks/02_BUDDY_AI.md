# Chess Corp — POC 02: Buddy sterowany przez Meta Muse Spark

## 1. Kontekst projektu

Projekt Chess Corp ma już działający, grywalny prototyp POC 01.

Aktualnie zaimplementowano:

- Grę 2D w Pygame CE.
- Uruchamianie w przeglądarce przez pygbag.
- Docker Compose.
- Oryginalne grafiki w katalogu `grafika/`.
- Poruszanie postacią za pomocą WASD.
- Interakcje klawiszem E.
- NPC o imieniu Buddy.
- System dialogowy.
- Pierwszy quest „Pierwszy dzień w Chess Corp”.
- Możliwość ukończenia questu.
- Ponowne rozpoczęcie rozgrywki.

Gra jest dostępna pod adresem:

`http://localhost:8080`

**Wszystkie powyższe funkcjonalności muszą nadal działać po ukończeniu POC 02.**

Nie twórz nowego projektu. Rozbuduj istniejące repozytorium.

## 2. Cel POC 02

Dodaj możliwość swobodnej rozmowy tekstowej z Buddy'm, wykorzystując Meta Muse Spark przez Meta Model API.

Oczekiwane zachowanie:

1. Gracz podchodzi do Buddy'ego.
2. Naciska E.
3. Otwiera się okno rozmowy.
4. Gracz może wpisać dowolną wiadomość.
5. Wiadomość trafia do backendu FastAPI.
6. Backend wysyła zapytanie do Meta Muse Spark.
7. Buddy odpowiada zgodnie ze swoją osobowością i kontekstem gry.
8. Gracz może kontynuować rozmowę.
9. Historia rozmowy jest zachowywana podczas sesji.
10. Po zamknięciu dialogu gracz może normalnie kontynuować rozgrywkę.

Przykład:

Gracz:

„Buddy, dlaczego nie mogę wejść do tego budynku?”

Buddy:

„Oficjalnie potrzebujesz identyfikatora. Nieoficjalnie... powiedzmy, że nie wszystkie drzwi w Chess Corp prowadzą tam, gdzie powinny.”

Odpowiedzi mają być generowane przez AI, a nie wybierane z wcześniej przygotowanej listy.

## 3. Priorytety

Najważniejszy jest działający prototyp.

Kolejność priorytetów:

1. Zachowanie funkcjonalności POC 01.
2. Działające połączenie z backendem.
3. Działające połączenie z Muse Spark.
4. Swobodna rozmowa.
5. Historia konwersacji.
6. Obsługa błędów.
7. Testy.
8. Drobne poprawki interfejsu.

Nie implementuj jeszcze:

- Generowania nowych NPC.
- Generowania questów przez AI.
- Generowania grafik.
- Rozbudowanej pamięci długoterminowej.
- Systemu agentów wieloosobowych.
- Rozpoznawania mowy.
- Syntezy głosu.
- Bazy wektorowej.
- Panelu AI Director Studio.

To będą kolejne etapy.

## 4. Technologie

Wykorzystaj:

- Python 3.12+.
- Pygame CE.
- pygbag.
- FastAPI.
- httpx.
- Pydantic.
- uv.
- pytest.
- Docker Compose.
- Meta Model API.

Nie zmieniaj obecnego silnika ani sposobu uruchamiania gry.

## 5. Analiza istniejącego projektu

Przed implementacją:

1. Przeczytaj `AGENTS.md`.
2. Przeanalizuj strukturę repozytorium.
3. Sprawdź aktualną implementację dialogów.
4. Sprawdź obsługę interakcji E.
5. Sprawdź działanie systemu questów.
6. Sprawdź konfigurację Docker Compose.
7. Sprawdź sposób budowania gry przez pygbag.
8. Zidentyfikuj miejsca wymagające zmian.

Dostosuj implementację do istniejącego kodu.

Nie przepisuj działających mechanik bez potrzeby.

Nie nadpisuj oryginalnych grafik.

## 6. Backend FastAPI

Dodaj niewielki backend odpowiedzialny za komunikację z Meta Model API.

Wymagane endpointy:

### GET /health

Zwraca informację, czy backend działa.

Przykładowa odpowiedź:

```json
{
  "status": "ok"
}
```

### POST /api/chat

Przyjmuje wiadomość gracza i identyfikator sesji.

Przykładowe żądanie:

```json
{
  "session_id": "player-session-001",
  "npc_id": "buddy",
  "message": "Kim jesteś?",
  "language": "pl"
}
```

Przykładowa odpowiedź:

```json
{
  "session_id": "player-session-001",
  "npc_id": "buddy",
  "reply": "Jestem Buddy. Pomagam nowym pracownikom przetrwać pierwszy dzień.",
  "status": "ok"
}
```

Zdefiniuj modele Pydantic.

Waliduj długość wiadomości, język i identyfikator NPC.

Nie zwracaj użytkownikowi wewnętrznych wyjątków ani sekretów API.

## 7. Integracja Meta Muse Spark

Wykorzystaj oficjalne Meta Model API.

Przed implementacją sprawdź aktualną dokumentację:

https://dev.meta.ai/

Nie wymyślaj nazw modeli, endpointów ani parametrów.

Jeżeli dostępny jest oficjalny SDK odpowiedni do tego zadania, możesz go wykorzystać. W przeciwnym razie użyj `httpx`.

Konfiguracja ma pochodzić ze zmiennych środowiskowych.

Przewidź:

- Klucz API.
- Identyfikator modelu.
- Timeout.
- Opcjonalny adres bazowy API, jeżeli jest potrzebny.
- Tryb testowy bez prawdziwego API.

Nie umieszczaj klucza w kodzie.

Nie umieszczaj klucza w frontendzie Pygame.

Nie zapisuj klucza w repozytorium Git.

Nie wykonuj płatnych wywołań API bez wyraźnej zgody użytkownika.

Jeżeli nie ma klucza, aplikacja powinna nadal się uruchamiać i wyświetlać zrozumiały komunikat o niedostępności AI.

## 8. Osobowość Buddy'ego

Buddy jest pracownikiem korporacji Chess Corp.

Jego zadanie to pomoc nowemu pracownikowi w pierwszym dniu.

Charakter:

- Przyjazny.
- Lekko ironiczny.
- Zna zasady korporacji.
- Nie ufa całkowicie kierownictwu.
- Czasami sugeruje, że korporacja ukrywa tajemnice.
- Nie zdradza wszystkiego od razu.
- Nie jest wszechwiedzący.

Buddy powinien odpowiadać naturalnie, jak postać z gry.

Nie powinien przedstawiać się jako model językowy.

Powinien mówić po polsku albo angielsku, zależnie od wybranego języka.

Nie powinien samodzielnie zmieniać stanu gry.

W POC 02 AI odpowiada wyłącznie za dialog.

## 9. Kontekst gry

Backend powinien otrzymywać minimalny kontekst aktualnej rozgrywki.

Przykładowo:

```json
{
  "quest_id": "first_day",
  "quest_status": "in_progress",
  "has_badge": false
}
```

Wykorzystaj kontekst do przygotowania odpowiedzi Buddy'ego.

Przykład:

Jeżeli gracz nie ma identyfikatora, Buddy może przypomnieć o zadaniu.

Jeżeli gracz ukończył quest, Buddy powinien o tym wiedzieć.

**Ważne:** stan gry jest ustalany przez istniejący silnik, nie przez model AI.

Nie pozwalaj modelowi samodzielnie potwierdzać ukończenia questu ani przyznawać przedmiotów.

Nie traktuj danych kontekstowych przesyłanych przez przeglądarkę jako zaufanych danych bezpieczeństwa. Na potrzeby POC można użyć ich do dialogu, ale nie do autoryzacji działań.

## 10. Historia rozmowy

W POC 02 wystarczy pamięć sesyjna.

Nie potrzebujemy jeszcze SQLite.

Przechowuj historię na backendzie w prostym repozytorium pamięciowym.

Historia powinna:

- Być oddzielna dla każdej sesji.
- Zachowywać kolejność wiadomości.
- Mieć ograniczoną długość.
- Być przekazywana do modelu jako kontekst.
- Nie mieszać rozmów różnych graczy.

Przygotuj interfejs umożliwiający późniejsze zastąpienie pamięci przez SQLite.

Nie buduj teraz rozbudowanego systemu pamięci NPC.

## 11. Interfejs rozmowy w Pygame

Rozbuduj istniejący system dialogowy.

Wymagania:

- Interakcja E otwiera rozmowę z Buddy'm.
- Gracz może wpisywać tekst.
- Enter wysyła wiadomość.
- Widoczna jest wiadomość gracza.
- Widoczna jest odpowiedź Buddy'ego.
- Podczas oczekiwania wyświetla się informacja „Buddy pisze...”.
- Esc zamyka rozmowę.
- Po zamknięciu można dalej poruszać postacią.
- Długie wiadomości są zawijane.
- Pole tekstowe nie wychodzi poza ekran.
- Obsługiwane są polskie znaki.

Zachowaj istniejącą estetykę pixel art.

Wykorzystaj obecne kolory interfejsu.

Nie zastępuj całego UI nowym frameworkiem.

## 12. Asynchroniczność

Gra musi pozostać responsywna podczas oczekiwania na odpowiedź AI.

Nie wykonuj blokujących zapytań HTTP w