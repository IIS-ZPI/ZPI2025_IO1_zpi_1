# CERCAS – Test Suite Report

---

## How to Run Tests

### Prerequisites

```bash
pip install -e .
pip install pytest python-dateutil requests
```

### Commands

**macOS / Linux**
```bash
source .venv/bin/activate
pytest
```

**Windows – Command Prompt**
```cmd
set PYTHONPATH=src\app
.venv\Scripts\pytest
```

**Windows – PowerShell**
```powershell
$env:PYTHONPATH = "src\app"
.venv\Scripts\pytest
```

### Single file
```bash
pytest tests/test_main.py
```

### Result codes
| Symbol | Meaning |
|--------|---------|
| `OK` | Test passed — behaviour matches expectation |
| `FAILED` | Assertion not met — bug found in production code or test logic |
| `ERROR` | Test could not run — environment or import problem |

---

## Test Files Overview

| # | File | Tests | Type |
|---|------|------:|------|
| 1 | `test_currency_validator.py` | 13 | Unit |
| 2 | `test_cercas_set_methods.py` | 23 | Unit |
| 3 | `test_cercas_show_config.py` | 15 | Unit |
| 4 | `test_main.py` | 20 | Unit + Integration |
| 5 | `test_exchange_rates_calculations.py` | 22 | Unit (real NBP fixtures) |
| 6 | `test_run_analysis.py` | 12 | Unit (class-based) |
| 7 | `test_shell.py` | 28 | Integration |
| 8 | `test_acceptance.py` | 12 | Acceptance |
| | **TOTAL** | **145** | |

---

## Section 1 — `test_currency_validator.py`

Validates the `currency_validator` module: ISO 4217 format checking and NBP API currency lookup. All network calls are replaced with mocks — tests run fully offline.

### 1.1 `is_iso4217_format`

| Test | Description | Result |
|------|-------------|--------|
| `test_is_iso4217_format_1` | "PLN" — valid 3-letter uppercase → accepted | OK |
| `test_is_iso4217_format_2` | "PL" — 2 letters → rejected | OK |
| `test_is_iso4217_format_3` | "pln" — lowercase → rejected | OK |
| `test_is_iso4217_format_4` | "PLNA" — 4 letters → rejected | OK |
| `test_is_iso4217_format_5` | "NLP" — valid format → accepted | OK |
| `test_is_iso4217_format_digits_rejected` | "US1" — contains digit → rejected | OK |
| `test_is_iso4217_format_empty_string_rejected` | empty string → rejected | OK |
| `test_is_iso4217_format_special_chars_rejected` | "EU€" — special character → rejected | OK |

### 1.2 `validate_currency` (mocked NBP API)

| Test | Description | Result |
|------|-------------|--------|
| `test_226_validate_currency_accepts_code_in_nbp_table` | Code present in mocked NBP list → no exception | OK |
| `test_226_validate_currency_raises_for_code_not_in_nbp` | Code absent from NBP → ValueError | OK |
| `test_226_validate_currency_accepts_pln_without_api_call` | PLN is always valid (NBP base currency) | OK |
| `test_261_validate_currency_raises_for_bad_format_before_api_check` | Bad format short-circuits before the API call | OK |
| `test_226_validate_currency_raises_for_lowercase_code` | Lowercase code → ValueError | OK |

---

## Section 2 — `test_cercas_set_methods.py`

Unit tests for the four CERCAS configuration setters. Each test is mapped to the corresponding SRS requirement. All NBP calls are mocked.

### 2.1 `set_pair` (SRS 2.1.1 / 2.6.1)

| Test | Description | Result |
|------|-------------|--------|
| `test_211_set_pair_stores_base_and_quote` | Valid pair stores `base` and `quote` attributes | OK |
| `test_211_set_pair_converts_lowercase_input_to_uppercase` | "eur"/"usd" normalised to "EUR"/"USD" | OK |
| `test_211_set_pair_prints_success_message` | Confirmation message printed on success | OK |
| `test_261_set_pair_rejects_too_short_currency_code` | "EU" (2 chars) → error, `base` stays None | OK |
| `test_261_set_pair_rejects_too_long_currency_code` | "EURO" (4 chars) → error | OK |
| `test_261_set_pair_rejects_currency_not_in_nbp` | Code not in NBP → error | OK |
| `test_261_set_pair_does_not_partially_set_on_invalid_quote` | Invalid quote → `base` also not stored | OK |

### 2.2 `set_start` (SRS 2.1.2 / 2.2.5)

End date is not stored — it is derived from `start_date` and `aggregation_type` via `__get_end_date()`.

| Test | Description | Result |
|------|-------------|--------|
| `test_212_set_start_stores_start_date` | Valid date stored in `start_date` attribute | OK |
| `test_212_set_start_prints_success_message` | Confirmation message printed on success | OK |
| `test_225_set_start_rejects_date_before_2002_01_02` | Date before 2002-01-02 → error, `start_date` stays None | OK |
| `test_225_set_start_accepts_date_on_2002_01_02` | 2002-01-02 is the earliest allowed start date | OK |
| `test_212_set_start_rejects_future_date` | Future start date → error | OK |
| `test_212_end_date_derived_as_start_plus_30_days_for_monthly` | MONTHLY: start+30d derived correctly | OK |
| `test_212_end_date_derived_as_start_plus_90_days_for_quarterly` | QUARTERLY: start+90d derived correctly | OK |

### 2.3 `set_type` (SRS 2.1.3)

| Test | Description | Result |
|------|-------------|--------|
| `test_213_set_type_stores_monthly` | MONTHLY stored in `aggregation_type` | OK |
| `test_213_set_type_stores_quarterly` | QUARTERLY stored in `aggregation_type` | OK |
| `test_213_set_type_prints_success_message` | Confirmation message printed | OK |
| `test_213_set_type_can_switch_from_monthly_to_quarterly` | Switching between types allowed | OK |

### 2.4 `set_interval` (SRS 2.1.4 / 2.6.5)

| Test | Description | Result |
|------|-------------|--------|
| `test_214_set_interval_stores_positive_integer` | Value 5 stored correctly | OK |
| `test_214_set_interval_stores_value_of_1` | Minimum value 1 accepted | OK |
| `test_214_set_interval_prints_success_message` | Confirmation message printed | OK |
| `test_265_set_interval_rejects_negative_number` | Negative number → error | OK |
| `test_265_set_interval_rejects_zero` | Zero → error (not a positive integer) | OK |

---

## Section 3 — `test_cercas_show_config.py`

Unit tests for `CERCAS.show_config()`. Verifies that each configuration field is printed to stdout — either its current value or an "isn't set" message.

### 3.1 Currency pair

| Test | Description | Result |
|------|-------------|--------|
| `test_417_show_config_reports_base_not_set_when_none` | "isn't set" when pair not configured | OK |
| `test_417_show_config_reports_base_currency_when_set` | Base code appears in output | OK |
| `test_417_show_config_reports_quote_currency_when_set` | Quote code appears in output | OK |
| `test_417_show_config_does_not_print_base_value_when_pair_not_set` | "Base currency is:" absent when unset | OK |

### 3.2 Analysis period

| Test | Description | Result |
|------|-------------|--------|
| `test_417_show_config_reports_dates_not_set_when_none` | "isn't set" when period not configured | OK |
| `test_417_show_config_reports_start_date_when_set` | Start date appears in output | OK |
| `test_417_show_config_reports_end_date_monthly_when_start_and_aggregation_set` | Derived end date shown for MONTHLY | OK |
| `test_417_show_config_reports_end_date_quarterly_when_start_and_aggregation_set` | Derived end date shown for QUARTERLY | OK |
| `test_417_show_config_does_not_show_end_date_when_aggregation_not_set` | End date omitted until aggregation type is set | OK |

### 3.3 Aggregation type

| Test | Description | Result |
|------|-------------|--------|
| `test_417_show_config_reports_aggregation_not_set_when_none` | "isn't set" when type not configured | OK |
| `test_417_show_config_reports_monthly_when_set` | "monthly" appears when MONTHLY set | OK |
| `test_417_show_config_reports_quarterly_when_set` | "quarterly" appears when QUARTERLY set | OK |

### 3.4 Interval count

| Test | Description | Result |
|------|-------------|--------|
| `test_417_show_config_reports_intervals_not_set_when_none` | "isn't set" when intervals not configured | OK |
| `test_417_show_config_reports_interval_count_when_set` | Interval number appears in output | OK |
| `test_417_show_config_full_config_displays_all_fields` | All four fields appear when fully configured | OK |

---

## Section 4 — `test_main.py`

Unit and integration tests for the core computation pipeline. Every expected value is calculated manually from the SRS formulas — not derived from the source code.

### 4.1 Cross-rate computation (SRS 2.3.1)

| Test | Description | Result |
|------|-------------|--------|
| `test_231_cross_rate_is_base_pln_divided_by_quote_pln` | EUR/USD = EUR_PLN / USD_PLN | OK |
| `test_231_each_date_cross_rate_computed_independently` | Each date computed independently | OK |
| `test_231_pln_as_base_equals_one_divided_by_quote_pln_rate` | PLN/USD = 1 / USD_PLN | OK |
| `test_231_pln_as_quote_cross_rate_equals_base_pln_rate_directly` | EUR/PLN = EUR_PLN (no division) | OK |

### 4.2 Daily change computation (SRS 2.3.2)

| Test | Description | Result |
|------|-------------|--------|
| `test_232_daily_change_equals_current_rate_minus_previous_rate` | change = rate[d] − rate[d−1] | OK |
| `test_232_daily_change_is_negative_when_rate_falls` | Negative change when rate drops | OK |
| `test_232_n_sessions_produce_n_minus_1_daily_changes` | N rates → N−1 changes | OK |
| `test_232_three_consecutive_rates_produce_correct_two_changes` | Two-change sequence verified manually | OK |

### 4.3 Histogram construction (SRS 2.3.4)

| Test | Description | Result |
|------|-------------|--------|
| `test_234_histogram_step_width_equals_range_divided_by_n` | step = (max−min) / N | OK |
| `test_234_histogram_returns_exactly_n_bins` | Always exactly N bins | OK |
| `test_234_sum_of_all_bin_frequencies_equals_number_of_values` | No data lost across bins | OK |
| `test_234_maximum_value_is_placed_in_last_bin_not_overflowed` | Max value clamped to last bin | OK |
| `test_234_bin_frequencies_match_manual_calculation` | Frequencies match manual calculation | OK |

### 4.4 CSV export (SRS 2.4.1–2.4.3)

| Test | Description | Result |
|------|-------------|--------|
| `test_241_export_creates_a_file_on_disk` | CSV file created on disk | OK |
| `test_242_export_rejects_path_without_csv_extension` | Non-.csv path → error | OK |
| `test_243_first_line_of_csv_is_the_required_header` | Header = `interval_start;interval_end;frequency` | OK |
| `test_243_csv_data_rows_are_separated_by_semicolons` | Each row has 3 semicolon-separated fields | OK |
| `test_243_csv_frequency_values_match_manually_computed_histogram` | Exported frequencies match manual calculation | OK |

### 4.5 Full pipeline + Issue #28 regression

| Test | Description | Result |
|------|-------------|--------|
| `test_full_pipeline_eur_usd_histogram_matches_manual_calculation` | All SRS 2.3.x formulas produce correct histogram | OK |
| `test_issue28_exported_frequency_sum_equals_number_of_daily_changes` | **Issue #28 regression** — exported frequency sum equals number of daily changes | OK |

---

## Section 5 — `test_exchange_rates_calculations.py`

Unit tests for the core calculation pipeline using real historical NBP data as fixtures (EUR/PLN and USD/PLN, 2024-01-02 → 2024-02-01). No live API calls are made — all 23 trading-day rate values are embedded in the test file as constants obtained via `curl`.

### 5.1 `build_cross_rate_series`

| Test | Description | Result |
|------|-------------|--------|
| `test_cross_rate_eur_usd_series_length` | All 23 common dates are returned | OK |
| `test_cross_rate_eur_usd_first_value` | 2024-01-02: EUR/USD = 4.3434 / 3.9432 (exact) | OK |
| `test_cross_rate_eur_usd_last_value` | 2024-02-01: EUR/USD = 4.3247 / 4.0047 (exact) | OK |
| `test_cross_rate_eur_pln_direct` | quote=PLN → series equals EUR/PLN directly | OK |
| `test_cross_rate_pln_usd_inverse` | base=PLN → series equals 1 / USD/PLN | OK |
| `test_cross_rate_partial_date_overlap` | Only intersection of dates returned when inputs differ | OK |
| `test_cross_rate_dates_are_sorted` | Output dates are in ascending chronological order | OK |

### 5.2 `compute_daily_changes`

| Test | Description | Result |
|------|-------------|--------|
| `test_daily_changes_count` | 23 data points → 22 daily changes | OK |
| `test_daily_changes_first_value` | First change: series[1] − series[0] | OK |
| `test_daily_changes_last_value` | Last change: series[−1] − series[−2] | OK |
| `test_daily_changes_first_value_from_raw` | 2024-01-03 minus 2024-01-02, from raw NBP rates | OK |
| `test_daily_changes_last_value_from_raw` | 2024-02-01 minus 2024-01-31, from raw NBP rates | OK |
| `test_daily_changes_single_point_returns_empty` | Single data point → empty list (no change) | OK |

### 5.3 `build_histogram`

| Test | Description | Result |
|------|-------------|--------|
| `test_histogram_bin_count` | 22 changes, N=5 → exactly 5 bins | OK |
| `test_histogram_frequencies_sum_to_change_count` | Every change lands in exactly one bin | OK |
| `test_histogram_known_frequencies` | Bin frequencies [2,2,3,10,5] verified manually from NBP data | OK |
| `test_histogram_first_bin_starts_at_min` | First bin lower bound equals minimum change | OK |
| `test_histogram_last_bin_ends_at_max` | Last bin upper bound equals maximum change | OK |
| `test_histogram_bins_are_contiguous` | End of bin[i] equals start of bin[i+1] for all i | OK |
| `test_histogram_different_interval_count` | N=10 → 10 bins, all 22 changes accounted for | OK |
| `test_histogram_empty_input_raises` | Empty input → ValueError | OK |
| `test_histogram_all_identical_values_raises` | All-identical values → ValueError (trivial histogram) | OK |

---

## Section 6 — `test_run_analysis.py`

Class-based unit tests for `run_analysis()`. Uses `patch.object` to mock `fetch_rates`. Focuses on guard conditions, core success scenarios, and data insufficiency.

### 6.1 `TestRunAnalysisMissingConfig` — histogram must stay None

| Test | Description | Result |
|------|-------------|--------|
| `test_no_base_currency` | Missing base → histogram stays None | OK |
| `test_no_quote_currency` | Missing quote → histogram stays None | OK |
| `test_no_start_date` | Missing start_date → histogram stays None | OK |
| `test_no_aggregation_type` | Missing aggregation_type → histogram stays None | OK |
| `test_no_intervals` | Missing number_of_intervals → histogram stays None | OK |
| `test_zero_intervals` | zero intervals → ZeroDivisionError caught, histogram stays None | OK |

### 6.2 `TestRunAnalysisSuccess` — histogram must be populated

| Test | Description | Result |
|------|-------------|--------|
| `test_histogram_is_set_after_run` | Successful run sets histogram | OK |
| `test_histogram_has_exactly_n_intervals` | Histogram has exactly 5 bins | OK |
| `test_histogram_interval_count_is_respected` | Bin count matches n for n ∈ {1, 3, 7, 10} | OK |
| `test_rerun_overwrites_previous_histogram` | Re-run with n=7 replaces n=3 histogram | OK |

### 6.3 `TestRunAnalysisInsufficientData` — histogram must stay None

| Test | Description | Result |
|------|-------------|--------|
| `test_single_data_point` | Single data point → not enough for daily change → error | OK |
| `test_empty_rates` | Empty API response → error | OK |

---

## Section 7 — `test_shell.py`

Integration tests for `CERCASShell` (the `cmd.Cmd` CLI). Each command is invoked via `shell.onecmd(...)` and its effects verified through stdout capture or attribute inspection.

### 7.1 `set_pair` command (SRS 4.1.2)

| Test | Description | Result |
|------|-------------|--------|
| `test_412_shell_set_pair_accepts_valid_pair` | "EUR/USD" prints success | OK |
| `test_412_shell_set_pair_stores_base_and_quote` | `base == "EUR"`, `quote == "USD"` stored | OK |
| `test_412_shell_set_pair_prints_usage_on_bad_format` | "EURUSD" (no slash) prints usage hint | OK |
| `test_412_shell_set_pair_rejects_invalid_currency_code` | "EU/USD" prints error | OK |

### 7.2 `set_start` command (SRS 4.1.3)

| Test | Description | Result |
|------|-------------|--------|
| `test_413_shell_set_start_accepts_valid_date` | "2023-01-01" prints success | OK |
| `test_413_shell_set_start_stores_date` | `start_date` stored correctly | OK |
| `test_413_shell_set_start_prints_usage_on_bad_format` | Non-date input prints usage hint | OK |
| `test_413_shell_set_start_rejects_date_before_nbp_epoch` | Date before 2002-01-02 prints error | OK |
| `test_413_shell_set_start_rejects_future_date` | Future date prints error | OK |

### 7.3 `set_aggregation` command (SRS 4.1.4)

| Test | Description | Result |
|------|-------------|--------|
| `test_414_shell_set_aggregation_monthly_prints_success` | "MONTHLY" prints success | OK |
| `test_414_shell_set_aggregation_quarterly_prints_success` | "QUARTERLY" prints success | OK |
| `test_414_shell_set_aggregation_accepts_lowercase_input` | "monthly" accepted (case-insensitive) | OK |
| `test_414_shell_set_aggregation_invalid_prints_usage` | Invalid input prints usage hint (not an exception) | OK |

### 7.4 `run_analysis` command (SRS 4.1.5)

| Test | Description | Result |
|------|-------------|--------|
| `test_415_shell_run_analysis_prints_error_when_pair_not_set` | Error printed when pair missing | OK |
| `test_415_shell_run_analysis_prints_error_when_start_not_set` | Error printed when start date missing | OK |
| `test_415_shell_run_analysis_prints_error_when_aggregation_not_set` | Error printed when aggregation type missing | OK |
| `test_415_shell_run_analysis_prints_error_when_intervals_not_set` | Error printed when intervals missing | OK |

### 7.5 `export` command (SRS 4.1.6)

| Test | Description | Result |
|------|-------------|--------|
| `test_416_shell_export_prints_error_when_no_analysis_run` | Error printed when no histogram exists | OK |
| `test_416_shell_export_creates_csv_after_successful_analysis` | CSV created and contains "frequency" | OK |
| `test_416_shell_export_prints_error_on_non_csv_extension` | Non-.csv extension prints error | OK |

### 7.6 `show_config` command (SRS 4.1.7)

| Test | Description | Result |
|------|-------------|--------|
| `test_417_shell_show_config_prints_not_set_for_empty_config` | "isn't set" in empty config | OK |
| `test_417_shell_show_config_shows_pair_when_set` | Pair values appear in output | OK |
| `test_417_shell_show_config_shows_period_when_start_and_aggregation_set` | Start and derived end date appear in output | OK |
| `test_417_shell_show_config_shows_only_start_when_aggregation_missing` | Only start date shown until aggregation is set | OK |

### 7.7 `switch_aggregation` command (SRS 4.1.8)

| Test | Description | Result |
|------|-------------|--------|
| `test_418_switch_aggregation_command_exists` | `do_switch_aggregation` method exists on shell | OK |
| `test_418_switch_aggregation_monthly_to_quarterly` | MONTHLY → QUARTERLY, output confirms new type | OK |
| `test_418_switch_aggregation_quarterly_to_monthly` | QUARTERLY → MONTHLY, output confirms new type | OK |
| `test_418_switch_aggregation_prints_error_when_not_set` | Error printed when aggregation type not set | OK |

---

## Section 8 — `test_acceptance.py`

End-to-end acceptance tests simulating complete user workflows. The NBP API is fully mocked — tests run offline. Based on use-case diagrams from SRS v1.1.

### 8.1 UC-1: Happy path — configure, run, export

| Test | Description | Result |
|------|-------------|--------|
| `test_uc1_full_analysis_produces_histogram` | Full run produces histogram with 5 bins | OK |
| `test_uc1_histogram_frequencies_sum_to_number_of_daily_changes` | **Issue #28 regression** — frequency sum equals number of daily changes (3) | OK |
| `test_uc1_export_creates_valid_csv_file` | CSV created with correct header | OK |
| `test_uc1_export_csv_frequency_sum_matches_histogram` | CSV frequencies match in-memory histogram | OK |
| `test_uc1_quarterly_aggregation_produces_histogram` | Quarterly run produces histogram, frequency sum = 9 | OK |

### 8.2 UC-2: Invalid configuration prevents analysis

| Test | Description | Result |
|------|-------------|--------|
| `test_uc2_analysis_blocked_when_pair_missing` | Error printed + histogram stays None | OK |
| `test_uc2_analysis_blocked_when_start_missing` | Error printed + histogram stays None | OK |
| `test_uc2_export_blocked_before_analysis` | Export before run prints error | OK |
| `test_uc2_export_blocked_for_non_csv_extension` | `.txt` extension → error printed, file not created | OK |

### 8.3 UC-3: Reconfigure and re-run

| Test | Description | Result |
|------|-------------|--------|
| `test_uc3_user_can_change_pair_and_rerun` | Histogram changes after pair change + re-run | OK |
| `test_uc3_user_can_change_interval_and_rerun` | Bin count changes after interval change | OK |
| `test_uc3_user_can_switch_aggregation_type_and_rerun` | MONTHLY (3 daily changes) → QUARTERLY (9 daily changes) | OK |

---

## Known Bugs Documented by Tests

| Section | Test | Bug | Status |
|---------|------|-----|--------|
| *(none)* | — | All known bugs have been fixed | — |
