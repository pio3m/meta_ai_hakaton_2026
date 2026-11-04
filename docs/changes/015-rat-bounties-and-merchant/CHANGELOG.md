# 015 — Cyber-szczury, kontrakty i Nyx

Data: 2026-11-04.

- Grywalna walka wręcz ze szczurami na istniejącej ulicy: Spacja, kierunek ciosu, zasięg, cooldown, odrzut, obrażenia, pasek HP i teksty trafień.
- Dwa kontrakty Barmana: 3 zwykłe szczury i 5 mocniejszych. Deterministyczne zaliczenie, łup i jednorazowa wypłata.
- Kredyty, apteczki (H), pancerz, ulepszenie pałki, śmierć i powrót z zachowaniem postępu.
- Nowa autonomiczna postać Nyx w istniejącym barze: profil, cel, krótka pamięć, ruch i sklep obsługiwany klawiaturą.
- Dwa rzeczywiście wygenerowane assety Meta Muse Image 1.0: cyber-szczur i Nyx. Cache, alfa, formaty Pygame i lokalne klatki animacji. Oryginały w grafika/ nietknięte.
- World AI zna kontekst walki, kontraktu i ekonomii. Wciąż zwraca wyłącznie walidowany plan sześciu dotychczasowych akcji; silnik sam rozstrzyga trafienia, zakupy i nagrody.
- Inspector: podgląd obu nowych assetów, kontekst rozgrywki, decyzje Nyx i wykonanie planów. Zachowana autoryzacja właściciela oraz izolacja jury.
- Trwały globalny licznik wydatków World AI, cooldown liczony po odebraniu odpowiedzi, brak ponawiania generacji obrazu i brak automatycznego retry wywołania Meta.
- Poprawki regresji: jawna rozmowa ma pierwszeństwo przed automatycznym powitaniem; raport starszego planu pozostaje ważny po powrocie do jego lokacji.
- 274 testy automatyczne, testy Pygame, pygbag/Compose i scenariusze klawiaturowe w Chrome. Szczegóły, dowody i ograniczenia w REPORT.md.
