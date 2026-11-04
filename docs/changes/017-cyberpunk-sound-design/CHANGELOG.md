# 017 — POC 016: Cyberpunk Sound Design

- Cztery oryginalne lokalne ambienty: deszcz/miasto, przytłumiony bar, serwery i wentylacja lobby.
- Dziesięć efektów: rozmowa, drzwi, sklep otwarcie/zamknięcie, zakup, kredyty, zamach, trafienie, pokonanie szczura i leczenie.
- AudioManager na pygame.mixer: cache, jeden kanał ambientu, płynne przejścia, ograniczone kanały efektów i bezpieczny brak audio.
- Audio odblokowane po zaufanej interakcji użytkownika. M wycisza/włącza, tylko dyskretny napis przy wyciszeniu.
- Brak zmian mechaniki, questów, AI i dużych paneli UI. Brak nowych usług/frameworków i płatnego audio.
- Pakowanie PCM WAV do pygbag, rzeczywisty test miksera w Chrome i testy awarii.
- Na późniejsze polecenie użytkownika wszystkie tryby ustawione META, Docker zrestartowany, globalny limit World AI podniesiony do zatwierdzonych 50. Liczników nie resetowano.
