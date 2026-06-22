# Application Test Report No. 2

**2026-06-22** *(Report No. 1 dated 2026-06-11)*

---

## A. Description of Activities Performed.

**Environments and devices used for testing:**

1. Computer – macOS Tahoe 26.5.1 / Python 3.13, virtual environment `.venv`, VS Code editor

**Tester login and password:** wiktorrozanski (local macOS system user; CLI application – no login system)

**Build number:** `8f4286e` dated **2026-06-11**

### Application areas and types of tests performed:

| Application area | Types of tests performed | Time spent on testing |
|---|---|---|
| Currency validation (`currency_validator`) | unit tests, boundary value tests, validation tests (mocked NBP API) | 1 h |
| CERCAS configuration (`set_pair`, `set_period`, `set_type`, `set_interval`) | unit tests, boundary value tests, validation tests | 2 h |
| Configuration display (`show_config`) | unit tests, functional tests | 0.5 h |
| Data processing (cross-rate, daily changes, aggregation, histogram) | unit tests, regression tests (Issue #28) | 2 h |
| CSV export | unit tests, integration tests | 1 h |
| CLI interface (`CERCASShell`) | integration tests, functional tests | 1.5 h |
| Full application (UC-1, UC-2, UC-3) | acceptance tests, regression tests | 1.5 h |

---

## B. Summary of All Defects.

**1) Fixed and re-tested.**

a) **Bug #1 – `set_period` accepted equal start and end dates (SRS 2.6.3)**
Found: commit `447b2cf` (2026-06-09) · Fixed: commit `560bbe6` (2026-06-10)

b) **Bug #2 – `set_interval` accepted zero (SRS 2.6.5)**
Found: commit `447b2cf` (2026-06-09) · Fixed: commit `560bbe6` (2026-06-10)

c) **Bug #3 – Missing `switch_aggregation` command in the CLI interface (SRS 4.1.8)**
Found: commit `447b2cf` (2026-06-09) · Fixed: commit `560bbe6` (2026-06-10)

d) **Bug #4 – `do_set_aggregation` threw a `ValueError` exception instead of printing a message to the user**
Found: commit `447b2cf` (2026-06-09) · Fixed in the `else` branch of `do_set_aggregation` (now prints "Usage: set_aggregation...") · confirmed by test `test_414_shell_set_aggregation_invalid_prints_usage`

e) **Bug #5 – Test file `text_exchange_rates_calculations.py` was never discovered by pytest**
Found: 2026-06-22 · The file prefix `text_` instead of `test_` prevented pytest from collecting 22 tests. · Fixed: renamed to `test_exchange_rates_calculations.py`

f) **Bug #6 – Acceptance test `test_uc2_export_blocked_for_non_csv_extension` contained no assertion**
Found: 2026-06-22 · The test called `c.export("output.txt")` but never asserted anything, making it a vacuous pass. · Fixed: added `assert "error" in capsys.readouterr().out.lower()` and `assert not os.path.exists("output.txt")`

**2) To be done.**

*(none)*

**3) Those that are risky to fix at this moment.**

*(none)*

---

## C. Detailed Defect Descriptions

### Bug #1a – `set_period` accepted equal start and end dates

**Detected by:** Wiktor Różański

**Report in which detected:** current (Report No. 1)

**Priority:** High — a zero-length time range leads to empty analysis results or an exception during aggregation

**Reproducibility:** 100% — every call to `set_period` with identical start and end dates reproduces the bug

**Browser:** not applicable (CLI application)

**Location of the problem:** `src/app/core/cercas.py` → `set_period` method → date validation condition

**Steps to reproduce:**

1. Launch the application: `source .venv/bin/activate && python -m app`
2. Set the currency pair: `set_pair EUR/USD`
3. Set identical dates: `set_period 2023-06-01 2023-06-01`
4. Observe that the application accepts the configuration without raising an error

**Test result:** The `set_period` method accepted a configuration where `end_date == start_date`, even though SRS 2.6.3 requires the end date to be **strictly later** than the start date. The condition in the code read `if end_date < start_date`, which did not reject the equality case. Fix: changed to `if end_date <= start_date` in commit `560bbe6`.

---

### Bug #2a – `set_interval` accepted the value zero

**Detected by:** Wiktor Różański

**Report in which detected:** current (Report No. 1)

**Priority:** Critical — setting the interval count to 0 causes a `ZeroDivisionError` when `run_analysis` is called

**Reproducibility:** 100% — every call to `set_interval 0` reproduces the bug

**Browser:** not applicable (CLI application)

**Location of the problem:** `src/app/core/cercas.py` → `set_interval` method → value validation condition

**Steps to reproduce:**

1. Launch the application: `source .venv/bin/activate && python -m app`
2. Configure the currency pair and period
3. Call: `set_interval 0`
4. Observe that the application accepts the value without raising an error
5. Call `run_analysis` — the application raises `ZeroDivisionError`

**Test result:** The `set_interval` method used the condition `if number >= 0`, causing zero to be accepted as a valid interval count. SRS 2.6.5 requires the interval count to be a **positive integer**. Fix: changed to `if number > 0` in commit `560bbe6`.

---

### Bug #3a – Missing `switch_aggregation` command in the CLI interface

**Detected by:** Wiktor Różański

**Report in which detected:** current (Report No. 1)

**Priority:** Medium — the functionality defined in SRS 4.1.8 was completely unavailable to the CLI user

**Reproducibility:** 100% — the command did not exist in the code

**Browser:** not applicable (CLI application)

**Location of the problem:** `src/app/cli/shell.py` → `CERCASShell` class — missing `do_switch_aggregation` method

**Steps to reproduce:**

1. Launch the application: `source .venv/bin/activate && python -m app`
2. Set the aggregation type: `set_aggregation MONTHLY`
3. Enter the command: `switch_aggregation`
4. The shell returns: `*** Unknown syntax: switch_aggregation`

**Test result:** The `do_switch_aggregation` method was completely absent from the `CERCASShell` class. SRS 4.1.8 requires the `switch_aggregation` command to toggle the aggregation type between MONTHLY and QUARTERLY. Fix: added the `do_switch_aggregation` method calling `self.app.switch_type()` in commit `560bbe6`.

---

### Bug #4a – `do_set_aggregation` threw an exception instead of printing a message

**Detected by:** Wiktor Różański

**Report in which detected:** current (Report No. 1)

**Priority:** Low — the user error is not handled gracefully, but the application does not lose data

**Reproducibility:** 100% — every call to `set_aggregation <invalid_value>` reproduced the behaviour

**Browser:** not applicable (CLI application)

**Location of the problem:** `src/app/cli/shell.py` → `do_set_aggregation` method → `else` branch

**Steps to reproduce (historical):**

1. Launch the application: `source .venv/bin/activate && python -m app`
2. Enter an invalid value: `set_aggregation WEEKLY`
3. The shell raised an unhandled `ValueError: Invalid aggregation type` instead of printing a hint

**Test result:** When the user provided an unsupported aggregation type, the `do_set_aggregation` method executed `raise ValueError("Invalid aggregation type")` instead of printing a user-friendly message. **This defect has been fixed** — the `else` branch now executes `print("Usage: set_aggregation <type> (MONTHLY or QUARTERLY)")`. Confirmed by passing test `test_414_shell_set_aggregation_invalid_prints_usage`.

---

### Bug #5a – Test file `text_exchange_rates_calculations.py` never discovered by pytest

**Detected by:** Wiktor Różański

**Report in which detected:** Report No. 2 (2026-06-22)

**Priority:** High — 22 unit tests using real historical NBP data fixtures were silently never executed

**Reproducibility:** 100% — pytest's default collection rule requires filenames to start with `test_`

**Browser:** not applicable (CLI application)

**Location of the problem:** `tests/text_exchange_rates_calculations.py` — incorrect filename prefix (`text_` instead of `test_`)

**Steps to reproduce:**

1. Run `pytest --collect-only` and observe the file is absent from the collected list
2. Note that 22 tests covering `build_cross_rate_series`, `compute_daily_changes`, and `build_histogram` with real NBP historical data are never run

**Test result:** File renamed to `test_exchange_rates_calculations.py`. All 22 tests pass. Total test count increased from 123 to 145.

---

### Bug #6a – Acceptance test `test_uc2_export_blocked_for_non_csv_extension` contained no assertion

**Detected by:** Wiktor Różański

**Report in which detected:** Report No. 2 (2026-06-22)

**Priority:** Medium — the test would pass even if the underlying code did not print an error or created the file

**Reproducibility:** 100% — the test body ended without any `assert` statement

**Browser:** not applicable (CLI application)

**Location of the problem:** `tests/test_acceptance.py` → `test_uc2_export_blocked_for_non_csv_extension`

**Steps to reproduce:**

1. Remove the error-printing logic from `CERCAS.export()`
2. Run the test — it still passes despite the bug in production code

**Test result:** Added `assert "error" in capsys.readouterr().out.lower()` to verify the error message is printed, and `assert not os.path.exists("output.txt")` to confirm no file is created. Both assertions now pass.

---

## D. Summary of Test Completion Criteria.

**1. Were we able to carry out the planned tests?**

Yes. All 145 tests listed in `Tests_Manual.md` were executed and completed with an OK status. All key application areas are covered: currency validation, configuration setters, `show_config`, core calculation pipeline (cross-rate, daily changes, histogram), CSV export, the CLI interface, and end-to-end acceptance tests (UC-1, UC-2, UC-3). In this report (No. 2) two additional bugs were discovered and fixed (Bugs #5 and #6), bringing the total test count from 123 to 145.

**2. Were there any difficulties?**

During the first run of the test suite (`testy_vol2`, commit `447b2cf`) three tests were intentionally failing — they were tests designed to expose known bugs in the production code (Bugs #1, #2, #3). Fixing those defects (commit `560bbe6`, 2026-06-10) caused all tests to pass. Before merging into the `develop` branch, it was also necessary to fix the application launch (commit `9a3e3da`) following modifications introduced by the tests — the `src/app/__main__.py` file required an import correction.

In Report No. 2 (2026-06-22) a discrepancy was found between `Tests_Manual.md` (which described non-existent test names and a file called `test_run_analisys.py`) and the actual test suite. The root cause was that `text_exchange_rates_calculations.py` was never renamed to `test_exchange_rates_calculations.py`, leaving 22 tests undiscovered. The manual was rewritten to match the actual state of the code.

**3. Time estimate verification.**

The estimated total testing time for the first report was approx. **9.5 h**. The actual time was close to the estimate. The additional triage and fixes in Report No. 2 (renaming the file, fixing the vacuous acceptance test, rewriting the manual) took approximately **1 h**.

**4. Risks that materialised.**

- Risk: "Missing CLI commands" — materialised (Bug #3, missing `switch_aggregation`). **Removed from test plan.**
- Risk: "Incorrect validation of date ranges and interval values" — materialised (Bug #1 and Bug #2). **Removed from test plan.**
- Risk: "User error handling inconsistency in CLI" — materialised (Bug #4). **Fixed and removed from test plan.**
- New risk discovered: silent test gaps caused by naming conventions (Bug #5 — `text_` prefix). All test files should be reviewed to ensure they start with `test_`.
- New risk discovered: acceptance tests without assertions can create false confidence. All acceptance tests should be audited for meaningful `assert` statements.

**5. Lessons learned.**

- Boundary conditions (`<` vs `<=`, `> 0` vs `>= 0`) are a frequent source of off-by-one errors. For every validation condition, a boundary value test should be written immediately alongside the implementation.
- CLI methods (`do_*`) should consistently handle all exceptions internally — they should never propagate them to the user. Unifying the `try/except → print(usage)` pattern across all `do_*` methods will eliminate this entire class of potential bugs.
- Every acceptance test must contain at least one `assert` statement. A test body that merely calls the production function without asserting anything is no better than no test at all — it will always pass regardless of whether the code is correct.
- Test file naming must follow the `test_*.py` convention. Any file starting with `text_`, `tests_`, or another prefix will be silently skipped by pytest, creating gaps in coverage with no visible indication of the problem.
