# Raport z testów aplikacji nr 1

**2026-06-11**

---

## A. Opis wykonanych działań.

**Środowiska i urządzenia, na których odbywały się testy:**

1. Komputer – macOS Tahoee 26.5.1 / Python 3.13, środowisko wirtualne `.venv`, edytor VS Code


**Login i hasło testera:** wiktorrozanski (lokalny użytkownik systemowy macOS; aplikacja CLI – brak systemu logowania)

**Build number:** `8f4286e` z dnia **2026-06-11**

### Obszary aplikacji oraz rodzaje testów wykonane:

| Obszar aplikacji | Rodzaje wykonanych testów | Czas poświęcony na testy |
|---|---|---|
| Walidacja walut (`currency_validator`) | testy jednostkowe, testy wartości brzegowych, testy walidacji (mocked NBP API) | 1 h |
| Konfiguracja CERCAS (`set_pair`, `set_period`, `set_type`, `set_interval`) | testy jednostkowe, testy wartości brzegowych, testy walidacji | 2 h |
| Wyświetlanie konfiguracji (`show_config`) | testy jednostkowe, testy funkcjonalne | 0,5 h |
| Przetwarzanie danych (cross-rate, zmiany dzienne, agregacja, histogram) | testy jednostkowe, testy regresji (Issue #28) | 2 h |
| Eksport CSV | testy jednostkowe, testy integracyjne | 1 h |
| Interfejs CLI (`CERCASShell`) | testy integracyjne, testy funkcjonalne | 1,5 h |
| Cała aplikacja (UC-1, UC-2, UC-3) | testy akceptacyjne, testy regresji | 1,5 h |

---

## B. Podsumowanie wszystkich defektów.

**1) Poprawione i zretestowane.**

a) **Bug #1 – `set_period` akceptował równe daty startową i końcową (SRS 2.6.3)**
Znaleziony: commit `447b2cf` (2026-06-09) · Naprawiony: commit `560bbe6` (2026-06-10)

b) **Bug #2 – `set_interval` akceptował zero (SRS 2.6.5)**
Znaleziony: commit `447b2cf` (2026-06-09) · Naprawiony: commit `560bbe6` (2026-06-10)

c) **Bug #3 – Brak komendy `switch_aggregation` w interfejsie CLI (SRS 4.1.8)**
Znaleziony: commit `447b2cf` (2026-06-09) · Naprawiony: commit `560bbe6` (2026-06-10)

d) **Bug #4 – `do_set_aggregation` rzuca wyjątek `ValueError` zamiast wypisać komunikat użytkownikowi**
Lokalizacja: `src/app/cli/shell.py` · wykryty testem `test_414_shell_set_aggregation_invalid_raises_instead_of_printing_error`

**2) Do zrobienia.**

*(brak)*

**3) Takie, które są ryzykowne do poprawienia w danym momencie.**

*(brak)*

---

## C. Szczegółowy opis defektów

### Bug #1a – `set_period` akceptował równe daty startową i końcową

**Kto wykrył:** Wiktor Różański

**Raport, w którym wykryty:** bieżący (Raport nr 1)

**Priorytet:** Wysoki — zerowy przedział czasu prowadzi do pustych wyników analizy lub wyjątku podczas aggregacji

**Powtarzalność:** 100% — każde wywołanie `set_period` z identyczną datą startową i końcową reprodukuje błąd

**Przeglądarka:** nie dotyczy (aplikacja CLI)

**Lokalizacja występowania problemu:** `src/app/core/cercas.py` → metoda `set_period` → warunek weryfikacji dat

**Kroki do powtórzenia:**

1. Uruchomić aplikację: `source .venv/bin/activate && python -m app`
2. Ustawić parę walut: `set_pair EUR/USD`
3. Ustawić identyczne daty: `set_period 2023-06-01 2023-06-01`
4. Zaobserwować, że aplikacja przyjmuje konfigurację bez zgłoszenia błędu

**Rezultat testów:** Metoda `set_period` akceptowała konfigurację, w której `end_date == start_date`, choć SRS 2.6.3 wymaga, aby data końcowa była **ściśle późniejsza** od daty startowej. Warunek w kodzie brzmiał `if end_date < start_date`, co nie odrzucało przypadku równości. Poprawka: zmiana na `if end_date <= start_date` w commit `560bbe6`.

---

### Bug #2a – `set_interval` akceptował wartość zero

**Kto wykrył:** Wiktor Różański

**Raport, w którym wykryty:** bieżący (Raport nr 1)

**Priorytet:** Krytyczny — ustawienie interwałów na 0 powoduje `ZeroDivisionError` przy wywołaniu `run_analysis`

**Powtarzalność:** 100% — każde wywołanie `set_interval 0` reprodukuje błąd

**Przeglądarka:** nie dotyczy (aplikacja CLI)

**Lokalizacja występowania problemu:** `src/app/core/cercas.py` → metoda `set_interval` → warunek walidacji wartości

**Kroki do powtórzenia:**

1. Uruchomić aplikację: `source .venv/bin/activate && python -m app`
2. Skonfigurować parę walut i okres
3. Wywołać: `set_interval 0`
4. Zaobserwować, że aplikacja przyjmuje wartość bez błędu
5. Wywołać `run_analysis` — aplikacja zgłasza `ZeroDivisionError`

**Rezultat testów:** Metoda `set_interval` używała warunku `if number >= 0`, przez co zero było akceptowane jako prawidłowa liczba interwałów. SRS 2.6.5 wymaga, aby liczba interwałów była **dodatnią liczbą całkowitą**. Poprawka: zmiana na `if number > 0` w commit `560bbe6`.

---

### Bug #3a – Brak komendy `switch_aggregation` w interfejsie CLI

**Kto wykrył:** Wiktor Różański

**Raport, w którym wykryty:** bieżący (Raport nr 1)

**Priorytet:** Średni — funkcjonalność zdefiniowana w SRS 4.1.8 była całkowicie niedostępna dla użytkownika CLI

**Powtarzalność:** 100% — komenda nie istniała w kodzie

**Przeglądarka:** nie dotyczy (aplikacja CLI)

**Lokalizacja występowania problemu:** `src/app/cli/shell.py` → klasa `CERCASShell` — brak metody `do_switch_aggregation`

**Kroki do powtórzenia:**

1. Uruchomić aplikację: `source .venv/bin/activate && python -m app`
2. Ustawić typ agregacji: `set_aggregation MONTHLY`
3. Wpisać komendę: `switch_aggregation`
4. Shell zwraca: `*** Unknown syntax: switch_aggregation`

**Rezultat testów:** Metoda `do_switch_aggregation` była całkowicie nieobecna w klasie `CERCASShell`. SRS 4.1.8 wymaga, aby komenda `switch_aggregation` przełączała typ agregacji między MONTHLY a QUARTERLY. Poprawka: dodanie metody `do_switch_aggregation` wywołującej `self.app.switch_type()` w commit `560bbe6`.

---

### Bug #4a – `do_set_aggregation` rzuca wyjątek zamiast wypisać komunikat

**Kto wykrył:** Wiktor Różański

**Raport, w którym wykryty:** bieżący (Raport nr 1)

**Priorytet:** Niski — błąd użytkownika nie jest gracefully obsługiwany, ale aplikacja nie traci danych

**Powtarzalność:** 100% — każde wywołanie `set_aggregation <nieprawidłowa_wartość>` reprodukuje zachowanie

**Przeglądarka:** nie dotyczy (aplikacja CLI)

**Lokalizacja występowania problemu:** `src/app/cli/shell.py` → metoda `do_set_aggregation` → gałąź `else`

**Kroki do powtórzenia:**

1. Uruchomić aplikację: `source .venv/bin/activate && python -m app`
2. Wpisać nieprawidłową wartość: `set_aggregation WEEKLY`
3. Shell rzuca nieobsługiwany wyjątek `ValueError: Invalid aggregation type` zamiast wypisać podpowiedź

**Rezultat testów:** Gdy użytkownik poda nieobsługiwany typ agregacji, metoda `do_set_aggregation` wykonuje `raise ValueError("Invalid aggregation type")` zamiast wypisać przyjazny komunikat (np. `Usage: set_aggregation <MONTHLY|QUARTERLY>`). W kodzie obecna jest nawet zakomentowana linia z poprawnym rozwiązaniem (`#print("Usage: set_type <type>")`). Defekt nadal obecny — wymaga poprawy w kolejnym sprincie.

---

## D. Podsumowanie kryteriów zakończenia wszystkich testów.

**1. Czy udało nam się zrealizować zaplanowane testy?**

Tak. Wszystkie 130 testów opisanych w TESTS.md zostało uruchomione i zakończonych statusem OK po naprawieniu wykrytych defektów. Pokryto wszystkie kluczowe obszary aplikacji: walidację, konfigurację, przetwarzanie danych, eksport CSV oraz interfejs CLI, w tym testy akceptacyjne end-to-end (UC-1, UC-2, UC-3).

**2. Czy wystąpiły jakieś trudności?**

Podczas pierwszego uruchomienia zestawu testów (`testy_vol2`, commit `447b2cf`) trzy testy celowo nie przechodziły — były to testy ujawniające znane błędy w kodzie produkcyjnym (Bugs #1, #2, #3). Naprawienie tych defektów przez DariuszPasińskiego (commit `560bbe6`, 2026-06-10) spowodowało, że wszystkie testy przeszły. Przed scaleniem z gałęzią `develop` konieczne było też naprawienie uruchamiania aplikacji (commit `9a3e3da`) po modyfikacjach wprowadzonych przez testy — plik `src/app/__main__.py` wymagał korekty importów.

**3. Weryfikacja estymat czasu pracy.**

Szacowany łączny czas testowania wyniósł ok. **9,5 h**. Faktyczny czas był zbliżony do estymaty — pisanie testów regresyjnych (szczególnie dla Issue #28 oraz testów akceptacyjnych UC-1–UC-3) okazało się nieznacznie bardziej czasochłonne ze względu na konieczność ręcznego wyliczenia oczekiwanych wartości z formuł SRS.

**4. Ryzyka, które się zrealizowały.**

- Ryzyko: „Brakujące komendy CLI" — zrealizowało się (Bug #3, brak `switch_aggregation`). Ryzyko można usunąć z test planu.
- Ryzyko: „Nieprawidłowa walidacja zakresów dat i interwałów" — zrealizowało się (Bug #1 i Bug #2). Ryzyko można usunąć z test planu.
- Nowe ryzyko do dodania do test planu: obsługa błędów użytkownika w CLI (Bug #4 nadal obecny — wszystkie komendy powinny być sprawdzone pod kątem jednolitej obsługi błędnych danych wejściowych).

**5. Wnioski na przyszłość.**

- Warunki graniczne (`<` vs `<=`, `> 0` vs `>= 0`) są częstym źródłem błędów off-by-one. Przy każdym warunku walidacji warto od razu pisać test dla wartości granicznej.
- Metody CLI (`do_*`) powinny konsekwentnie obsługiwać wszelkie wyjątki wewnętrznie — nigdy nie powinny propagować ich do użytkownika. Ujednolicenie wzorca `try/except → print(usage)` we wszystkich metodach `do_*` wyeliminuje całą klasę potencjalnych błędów.
- Testy akceptacyjne (UC-1–UC-3) wykryły regresję Issue #28 (eksport CSV gubił dane, gdy wszystkie wartości histogramu były identyczne) — warto rozbudować te testy o więcej scenariuszy granicznych danych wejściowych z NBP.
