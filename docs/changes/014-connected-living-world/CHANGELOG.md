# Living World Expansion — changelog

Data: 2026-11-04. Status: zakończony grywalny POC.

## Dodano

- Połączono centralną ulicę z trzema lokacjami: oryginalnym barem Cybroschligger, kryjówką hakerów i lobby Chess Corp. F obsługuje oznaczone drzwi, przejście ma fade i nazwę lokacji, Tab pokazuje mapę.
- Dziesięciu NPC łącznie, w tym Barman, Gościni, Cipher, Kontakt, Recepcja i Ochrona. Każdy ma rolę, cel, nastrój, pamięć, lokalne zachowania i zatrzymuje się do rozmowy.
- W każdej dodatkowej lokacji działa interakcja dodająca odrębny przedmiot: rachunek baru, fragment archiwum i przepustkę wizyty.
- Zachowanie stanu sesji między lokacjami: quest, ekwipunek, Buddy chat, dynamiczny quest, pozycje i pamięć NPC. NPC poza aktywnym ekranem nadal mają lokalną symulację.
- WorldPlanV2 z identyfikatorem lokacji, listą jej postaci i dozwolonych celów. Dotychczasowy WorldPlanV1 ulicy działa bez migracji. Model nie wykonuje kodu.
- AI Inspector pokazuje aktywną lokację, cele i źródła assetów także poprzez bezpłatną telemetrię, niezależnie od generacji planów.
- Backendowy Asset Generator wykorzystuje udokumentowane Muse Image 1.0. Jedna trwała próba, brak ponowień, cache PNG i metadanych, przetworzenie do 128×128, podgląd w Inspectorze. Wygenerowany znak naprawdę znajduje się na ścianie kryjówki.

## Zmieniono lub naprawiono

- Użyto oryginalnej grafiki baru, barmana i gościni. Wszystkie 476 oryginałów pozostają niezmienione. Nowe pliki są pochodnymi w assets/processed.
- Rozszerzono istniejący adapter, walidator i silnik sześciu akcji, bez nowego frameworka, bazy ani usługi.
- Wspólny licznik planów klienta obejmuje całą podróż, a limity serwera wszystkie sesje. Zmiana lokacji nie tworzy nowej zgody na koszty.
- Napisy źródeł odnoszą się do aktywnych działań, a lokalna pauza rozmowy nie jest raportowana jako decyzja Meta.
- Prywatny prompt assetu i znacznik wydatku nie trafiają do paczki przeglądarkowej ani Git. Właściciel może odczytać historyczny prompt z lokalnego cache; jury go nie widzi.
- Po teście wszystkie cztery integracje przywrócono do mock i wyłączono płatne zgody. Obraz Meta pozostaje w cache.

## Test LIVE

- 3 rzeczywiste World AI / Muse Spark 1.3: wszystkie plany poprawne; 7295 tokenów.
- 1 rzeczywista generacja Muse Image 1.0: sukces; 5387 tokenów referencyjnych, jedna grafika.
- 0 płatnych Buddy i Quest Director. Dalsze płatne próby zablokowane, kontenery LIVE zamknięte.

## Powiązania

Raport: [REPORT.md](REPORT.md). W tym etapie nie wykonywano commita.
