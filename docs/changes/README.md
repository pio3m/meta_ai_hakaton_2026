# Rejestr dużych zmian

Każda duża zmiana otrzymuje nowy katalog `NNN-krotki-slug/`, a w nim osobne pliki:

- `CHANGELOG.md`: co dodano, zmieniono, naprawiono lub usunięto.
- `REPORT.md`: cel, zakres, wykonane testy z wynikami, uruchomienie, ograniczenia i następny krok.
- `evidence/`: opcjonalne zrzuty i materiały weryfikacyjne bez sekretów lub prywatnych rozmów.

Numer jest kolejny w całym projekcie. Nie nadpisujemy zakończonych kart, aby opisać następną zmianę. W trakcie pracy można aktualizować kartę bieżącej zmiany; późniejsza duża poprawka otrzymuje nowy numer. Małe poprawki dokumentujemy w nowym pliku `NNN-slug/updates/YYYY-MM-DD-krotki-opis.md` powiązanej zmiany, z opisem zmiany i wynikiem sprawdzenia. Jeśli nazwa jest zajęta, dodaj kolejny numer.

Zacznij od [szablonu changelogu](_template/CHANGELOG.md) i [szablonu raportu](_template/REPORT.md). Wyniki historyczne zawsze oznaczaj jako historyczne. Nie zapisuj kluczy API, tokenów dostępu, cookies ani prywatnych promptów.

| Nr | Zmiana | Changelog | Raport |
|---|---|---|---|
| 001 | POC 01 — grywalna ulica | [Zmiany](001-poc01/CHANGELOG.md) | [Raport](001-poc01/REPORT.md) |
| 002 | POC 02 — rozmowa z Buddy’m | [Zmiany](002-buddy-ai/CHANGELOG.md) | [Raport](002-buddy-ai/REPORT.md) |
| 003 | Pierwsze prawdziwe wywołanie Muse Spark | [Zmiany](003-meta-live/CHANGELOG.md) | [Raport](003-meta-live/REPORT.md) |
| 004 | AI Inspector i widok jury | [Zmiany](004-ai-inspector/CHANGELOG.md) | [Raport](004-ai-inspector/REPORT.md) |
| 005 | Organizacja dokumentacji zmian | [Zmiany](005-change-documentation/CHANGELOG.md) | [Raport](005-change-documentation/REPORT.md) |
| 006 | POC 03 — AI Game Director | [Zmiany](006-ai-game-director/CHANGELOG.md) | [Raport](006-ai-game-director/REPORT.md) |
| 007 | POC 03 — rzeczywisty Director Muse Spark | [Zmiany](007-director-meta-live/CHANGELOG.md) | [Raport](007-director-meta-live/REPORT.md) |
| 008 | POC 03.5 — dynamiczne questy i zagadki | [Zmiany](008-dynamic-quests-puzzles/CHANGELOG.md) | [Raport](008-dynamic-quests-puzzles/REPORT.md) |
| 009 | DirectorPlanV2 — kontrolowany test Muse Spark LIVE | [Zmiany](009-director-v2-meta-live/CHANGELOG.md) | [Raport](009-director-v2-meta-live/REPORT.md) |
| 010 | POC 04 — NPC Guard | [Zmiany](010-npc-guard/CHANGELOG.md) | [Raport](010-npc-guard/REPORT.md) |

| 011 | Living AI World — czterech NPC i Muse Spark 1.3 | [Zmiany](011-living-ai-world/CHANGELOG.md) | [Raport](011-living-ai-world/REPORT.md) |
| 012 | Czytelny UI i wszystkie integracje mock | [Zmiany](012-readable-ui/CHANGELOG.md) | [Raport](012-readable-ui/REPORT.md) |
| 013 | NPC zatrzymują się do rozmowy | [Zmiany](013-npc-stop-and-talk/CHANGELOG.md) | [Raport](013-npc-stop-and-talk/REPORT.md) |
| 014 | Połączony Living World, oryginalny bar i Meta Image | [Zmiany](014-connected-living-world/CHANGELOG.md) | [Raport](014-connected-living-world/REPORT.md) |

| 015 | Cyber-szczury, kontrakty i Nyx / Meta LIVE | [Zmiany](015-rat-bounties-and-merchant/CHANGELOG.md) | [Raport](015-rat-bounties-and-merchant/REPORT.md) |

| 016 | Odsłonięta scena gry i statusy NPC w adminie | [Zmiany](016-unobstructed-game-ui/CHANGELOG.md) | [Raport](016-unobstructed-game-ui/REPORT.md) |

| 017 | POC 016 — Cyberpunk Sound Design | [Zmiany](017-cyberpunk-sound-design/CHANGELOG.md) | [Raport](017-cyberpunk-sound-design/REPORT.md) |

| 018 | Walka NPC, czat i nowe zlecenia sesji | [Zmiany](018-npc-combat-chat-and-session-jobs/CHANGELOG.md) | [Raport](018-npc-combat-chat-and-session-jobs/REPORT.md) |

| 019 | Lokalizacja EN/PL | [Zmiany](019-en-pl-localization/CHANGELOG.md) | [Raport](019-en-pl-localization/REPORT.md) |

| 020 | Profil płatny do nagrania demo | [Zmiany](020-live-demo-limits/CHANGELOG.md) | [Raport](020-live-demo-limits/REPORT.md) |

| 021 | Publiczne repozytorium GitHub | [Zmiany](021-public-github/CHANGELOG.md) | [Raport](021-public-github/REPORT.md) |
