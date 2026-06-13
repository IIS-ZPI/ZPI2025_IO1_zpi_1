# Application Test Report No. 2

**2026-06-13**

---

## A. Description of Activities Performed.

**Environments and devices used for testing:**

1. Computer – macOS Tahoe 26.5.1 / Python 3.13, virtual environment `.venv`, VS Code editor

**Tester login and password:** wiktorrozanski (local macOS system user; CLI application – no login system)

**Build number:** `develop` branch, dated **2026-06-13**

### Application areas and types of tests performed:

| Application area | Types of tests performed | Time spent on testing |
|---|---|---|
| Currency validation (`currency_validator`) | unit tests, boundary value tests, validation tests (mocked NBP API) | 1 h |
| CERCAS configuration (`set_pair`, `set_start`, `set_type`, `set_interval`) | unit tests, boundary value tests, validation tests | 2 h |
| Configuration display (`show_config`) | unit tests, functional tests | 0.5 h |
| Data processing (cross-rate, daily changes, aggregation, histogram) | unit tests, regression tests (Bug #5) | 3 h |
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

d) **Bug #5 – Histogram aggregation used calendar months/quarters instead of 30/90-day windows from start date (Annex 2.3.5 / 2.3.6)**
Found: 2026-06-13 · Fixed: 2026-06-13 (current report)

**2) To be done.**

*(none)*

**3) Those that are risky to fix at this moment.**

a) **Bug #4 – `do_set_aggregation` throws a `ValueError` exception instead of printing a message to the user**
Location: `src/app/cli/shell.py` · detected by test `test_414_shell_set_aggregation_invalid_raises_instead_of_printing_error`

---

## C. Detailed Defect Descriptions

### Bug #1a – `set_period` accepted equal start and end dates

**Detected by:** Wiktor Różański

**Report in which detected:** Report No. 1

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

**Report in which detected:** Report No. 1

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

**Report in which detected:** Report No. 1

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

**Report in which detected:** Report No. 1

**Priority:** Low — the user error is not handled gracefully, but the application does not lose data

**Reproducibility:** 100% — every call to `set_aggregation <invalid_value>` reproduces the behaviour

**Browser:** not applicable (CLI application)

**Location of the problem:** `src/app/cli/shell.py` → `do_set_aggregation` method → `else` branch

**Steps to reproduce:**

1. Launch the application: `source .venv/bin/activate && python -m app`
2. Enter an invalid value: `set_aggregation WEEKLY`
3. The shell raises an unhandled `ValueError: Invalid aggregation type` instead of printing a hint

**Test result:** When the user provides an unsupported aggregation type, the `do_set_aggregation` method executes `raise ValueError("Invalid aggregation type")` instead of printing a user-friendly message (e.g. `Usage: set_aggregation <MONTHLY|QUARTERLY>`). The defect remains present — requires fixing in a future sprint.

---

### Bug #5 – Histogram aggregation used calendar months/quarters instead of 30/90-day windows

**Detected by:** Wiktor Różański

**Report in which detected:** current (Report No. 2)

**Priority:** Critical — the histogram produced incorrect results for all analyses; the output data did not comply with Annex No. 1 requirements

**Reproducibility:** 100% — every `run_analysis` call reproduced the incorrect grouping

**Browser:** not applicable (CLI application)

**Location of the problem:** `src/app/core/cercas.py` → `get_period_key` method

**Root cause:** The original `get_period_key` returned `(date.year, date.month)` for MONTHLY and `(date.year, quarter)` for QUARTERLY. This grouped daily changes by calendar month (January, February, …) and calendar quarter (Q1, Q2, …), which violates Annex requirements 2.3.5 and 2.3.6.

Annex No. 1 specifies:
- **Monthly** (Req 2.3.5): one aggregation window = **30 consecutive days** starting from the user-selected start date.
- **Quarterly** (Req 2.3.6): one aggregation window = **90 consecutive days** starting from the user-selected start date.

**Steps to reproduce:**

1. Set start date to 2024-01-01, pair EUR/USD, MONTHLY aggregation, intervals 5.
2. Run analysis.
3. A change recorded on 2024-01-31 (day 30 from start) was incorrectly grouped into January's bucket (calendar month 0), whereas it should start a new 30-day window (window 1).
4. Similarly, a change on 2024-03-31 (day 90 from start) was grouped into Q1 instead of starting a new 90-day window.

**Test result:** The old test suite only checked whether the histogram existed and had N bins — it did not verify the grouping logic. The new tests explicitly expose this bug:

- `test_january_31st_is_window_1_not_window_0` — Jan 31 = day 30 → must be window 1
- `test_march_31_is_window_1_not_window_0` — Mar 31 = day 90 → must be window 1
- `test_january_spans_two_30_day_windows` — three changes in January alone must produce 2 buckets
- `test_q1_spans_two_90_day_windows` — changes on Mar 30 and Mar 31 must be in different buckets

**Fix:** `get_period_key` rewritten to compute `(date - start_date).days // 30` (MONTHLY) or `(date - start_date).days // 90` (QUARTERLY). `run_analysis` updated to derive `end_date` automatically (start + 29 days for MONTHLY, start + 89 days for QUARTERLY). New `set_start` command added (Annex 4.1.2).

---

## D. Summary of Test Completion Criteria.

**1. Were we able to carry out the planned tests?**

Yes. All 194 tests were executed and completed with an OK status after Bug #5 was fixed and the test suite was updated to reflect the requirements introduced by Annex No. 1. All key application areas were covered: validation, configuration, data processing (including 30/90-day window logic), CSV export, and the CLI interface, including end-to-end acceptance tests (UC-1, UC-2, UC-3).

**2. Were there any difficulties?**

The primary difficulty was identifying Bug #5. The previous test suite for `run_analysis` only verified the *existence* and *size* of the histogram — not the correctness of aggregation. Because the tests did not assert specific aggregated values or window boundaries, a fundamentally incorrect grouping (calendar months instead of 30-day windows) passed all checks undetected.

Additionally, the Annex changed three requirements simultaneously (2.1.2, 2.5.3, 2.6.3, 2.6.4, 4.1.2), requiring removal of 8 tests referencing the old `set_period` semantics and replacement with new `set_start` tests.

**3. Time estimate verification.**

The estimated total testing time for this report was approx. **10.5 h** (original 9.5 h + 1 h for Annex-related rework). The actual time was consistent with the estimate.

**4. Risks that materialised.**

- Risk: "Incorrect aggregation logic" — materialised (Bug #5, calendar-based grouping instead of fixed-day windows). The histogram was producing wrong results for every analysis run.
- Risk: "Tests not validating computation logic, only structural properties" — materialised. The old `run_analysis` tests checked only `len(histogram) == N`, not the values. This allowed Bug #5 to go undetected.

**5. Lessons learned.**

- **Test the logic, not just the shape.** Checking `len(histogram) == N` is not sufficient — tests must assert specific aggregated values computed by hand from the requirements. A histogram with 5 bins is correct in shape but completely wrong in content if the aggregation groups are wrong.
- **Changing requirements must trigger test invalidation.** When Annex No. 1 redefined "monthly" from calendar month to 30 consecutive days, existing tests remained green — they were testing the old (now-wrong) behaviour. A requirements change must be accompanied by a review of all tests that reference the affected section.
- **Boundary cases are the most revealing.** The clearest test of the 30/90-day window logic is a date that falls on the boundary: January 31 (day 30 from January 1) must be in window 1, not window 0. Writing this one boundary test immediately exposes the calendar-month bug.
