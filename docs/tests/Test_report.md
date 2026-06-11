# Application Test Report No. 1

**2026-06-11**

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

d) **Bug #4 – `do_set_aggregation` throws a `ValueError` exception instead of printing a message to the user**
Location: `src/app/cli/shell.py` · detected by test `test_414_shell_set_aggregation_invalid_raises_instead_of_printing_error`

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

### Bug #4a – `do_set_aggregation` throws an exception instead of printing a message

**Detected by:** Wiktor Różański

**Report in which detected:** current (Report No. 1)

**Priority:** Low — the user error is not handled gracefully, but the application does not lose data

**Reproducibility:** 100% — every call to `set_aggregation <invalid_value>` reproduces the behaviour

**Browser:** not applicable (CLI application)

**Location of the problem:** `src/app/cli/shell.py` → `do_set_aggregation` method → `else` branch

**Steps to reproduce:**

1. Launch the application: `source .venv/bin/activate && python -m app`
2. Enter an invalid value: `set_aggregation WEEKLY`
3. The shell raises an unhandled `ValueError: Invalid aggregation type` instead of printing a hint

**Test result:** When the user provides an unsupported aggregation type, the `do_set_aggregation` method executes `raise ValueError("Invalid aggregation type")` instead of printing a user-friendly message (e.g. `Usage: set_aggregation <MONTHLY|QUARTERLY>`). The code even contains a commented-out line with the correct solution (`#print("Usage: set_type <type>")`). The defect remains present — requires fixing in a future sprint.

---

## D. Summary of Test Completion Criteria.

**1. Were we able to carry out the planned tests?**

Yes. All 130 tests described in TESTS.md were executed and completed with an OK status after the detected defects were fixed. All key application areas were covered: validation, configuration, data processing, CSV export, and the CLI interface, including end-to-end acceptance tests (UC-1, UC-2, UC-3).

**2. Were there any difficulties?**

During the first run of the test suite (`testy_vol2`, commit `447b2cf`) three tests were intentionally failing — they were tests designed to expose known bugs in the production code (Bugs #1, #2, #3). Fixing those defects by DariuszPasiński (commit `560bbe6`, 2026-06-10) caused all tests to pass. Before merging into the `develop` branch, it was also necessary to fix the application launch (commit `9a3e3da`) following modifications introduced by the tests — the `src/app/__main__.py` file required an import correction.

**3. Time estimate verification.**

The estimated total testing time was approx. **9.5 h**. The actual time was close to the estimate — writing regression tests (particularly for Issue #28 and the UC-1–UC-3 acceptance tests) turned out to be slightly more time-consuming due to the need to manually calculate expected values from the SRS formulas.

**4. Risks that materialised.**

- Risk: "Missing CLI commands" — materialised (Bug #3, missing `switch_aggregation`). This risk can be removed from the test plan.
- Risk: "Incorrect validation of date ranges and interval values" — materialised (Bug #1 and Bug #2). This risk can be removed from the test plan.
- New risk to add to the test plan: user error handling in the CLI (Bug #4 still present — all commands should be reviewed for consistent handling of invalid user input).

**5. Lessons learned.**

- Boundary conditions (`<` vs `<=`, `> 0` vs `>= 0`) are a frequent source of off-by-one errors. For every validation condition, a boundary value test should be written immediately alongside the implementation.
- CLI methods (`do_*`) should consistently handle all exceptions internally — they should never propagate them to the user. Unifying the `try/except → print(usage)` pattern across all `do_*` methods will eliminate this entire class of potential bugs.
- The acceptance tests (UC-1–UC-3) caught the Issue #28 regression (the CSV export was losing data when all histogram values were identical) — it is worth extending these tests with more edge-case scenarios covering unusual NBP API data.
