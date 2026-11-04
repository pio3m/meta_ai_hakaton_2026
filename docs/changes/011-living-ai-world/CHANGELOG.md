# Living AI World — changelog

Data: 2026-11-04.

- Czterech animowanych NPC na istniejącej ulicy: Buddy, Security, Hacker i Employee. Kolory ról, aktualny stan, nastrój, dymki i dziennik wydarzeń; oryginalne grafiki pozostają niezmienione.
- Każda postać ma osobowość, cel i pamięć ostatnich sześciu zdarzeń. Lokalny świat działa od pierwszej klatki i bez dostępu do API.
- World AI jednym zapytaniem istniejącego adaptera Muse Spark planuje zachowania czterech postaci. Zamknięty kontrakt JSON i walidacja Pydantic oraz klienta; sześć dozwolonych akcji, zatwierdzone punkty ulicy, deterministyczny ruch i zakończenia/timeouty.
- Oddzielne WORLD_AI_MODE i WORLD_AI_ALLOW_PAID_REQUESTS; limity sesji, całego procesu, odstępu i tokenów. Brak ponowień HTTP; idempotencja rundy. Domyślnie mock i brak zgody na płatne wywołania.
- Inspector rozpoznaje World AI, pokazuje rzeczywisty payload właścicielowi, plan, walidację, tokeny, opóźnienie, cele i wykonanie; widok jury nadal ograniczony do demonstracyjnej sesji. Telemetria zachowuje zakończone akcje i oznacza ich źródło.
- Fallback przy błędzie, wolnym API, wyczerpaniu budżetu i zakończeniu planu. Etykiety META / MOCK / FALLBACK, osobne oznaczanie lokalnych odpowiedzi NPC i odtworzenia z cache.
- Poprawka odstępu zapytań po teście LIVE: zegar rzeczywisty i jedna sekunda marginesu. Poprawione skalowanie canvas do okna prezentacji oraz rozdzielone dymki.
- Zachowane Buddy chat, NPC Guard, pierwszy quest, DirectorPlanV1/V2 i trzy typy questów. Bez nowych frameworków, usług, baz i audio.
