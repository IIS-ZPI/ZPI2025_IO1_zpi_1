"""
Unit tests for CERCAS histogram generation.

Based on SRS v1.1 + Annex No. 1:
  Annex 2.3.5  monthly aggregation = 30 consecutive days from start date
  Annex 2.3.6  quarterly aggregation = 90 consecutive days from start date
  Annex 3.3    start date validation (end date is now derived, not user-set)
  Annex 4.1.2  set_start command replaces set_period

NOTE: this file imports from src.app.core.* (root-relative path).
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from app.core.aggregation_type import AggregationType
from app.core.cercas import CERCAS

EPS = 1e-9
START = datetime(2024, 1, 1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_cercas(**overrides) -> CERCAS:
    c = CERCAS()
    c.base = overrides.get("base", "USD")
    c.quote = overrides.get("quote", "EUR")
    c.start_date = overrides.get("start_date", START)
    c.aggregation_type = overrides.get("aggregation_type", AggregationType.MONTHLY)
    c.number_of_intervals = overrides.get("number_of_intervals", 5)
    return c


def _rates(start: datetime, count: int, base_rate: float = 4.0, step: float = 0.01):
    return [(start + timedelta(days=i), base_rate + i * step) for i in range(count)]


USD_RATES = _rates(START, 91, base_rate=4.00)
EUR_RATES = _rates(START, 91, base_rate=4.30)


def fake_fetch(currency):
    if currency == "USD":
        return USD_RATES
    if currency == "EUR":
        return EUR_RATES
    return []


# ===========================================================================
# get_period_key — Annex 2.3.5 (monthly = 30-day windows)
# ===========================================================================

class TestGetPeriodKeyMonthly:

    def test_start_date_itself_is_window_0(self):
        c = make_cercas(aggregation_type=AggregationType.MONTHLY)
        assert c.get_period_key(START) == 0

    def test_day_29_from_start_is_still_window_0(self):
        c = make_cercas(aggregation_type=AggregationType.MONTHLY)
        assert c.get_period_key(START + timedelta(days=29)) == 0

    def test_day_30_from_start_opens_window_1(self):
        c = make_cercas(aggregation_type=AggregationType.MONTHLY)
        assert c.get_period_key(START + timedelta(days=30)) == 1

    def test_day_59_from_start_is_still_window_1(self):
        c = make_cercas(aggregation_type=AggregationType.MONTHLY)
        assert c.get_period_key(START + timedelta(days=59)) == 1

    def test_day_60_from_start_opens_window_2(self):
        c = make_cercas(aggregation_type=AggregationType.MONTHLY)
        assert c.get_period_key(START + timedelta(days=60)) == 2

    def test_january_31st_is_window_1_not_window_0(self):
        c = make_cercas(aggregation_type=AggregationType.MONTHLY)
        jan_31 = datetime(2024, 1, 31)   # day 30 from 2024-01-01
        assert c.get_period_key(jan_31) == 1, (
            "BUG (Annex 2.3.5): Jan 31 is day 30 → window 1; "
            "calendar-month grouping wrongly puts it in January (window 0)"
        )


# ===========================================================================
# get_period_key — Annex 2.3.6 (quarterly = 90-day windows)
# ===========================================================================

class TestGetPeriodKeyQuarterly:

    def test_start_date_itself_is_window_0(self):
        c = make_cercas(aggregation_type=AggregationType.QUARTERLY)
        assert c.get_period_key(START) == 0

    def test_day_89_from_start_is_still_window_0(self):
        c = make_cercas(aggregation_type=AggregationType.QUARTERLY)
        assert c.get_period_key(START + timedelta(days=89)) == 0

    def test_day_90_from_start_opens_window_1(self):
        c = make_cercas(aggregation_type=AggregationType.QUARTERLY)
        assert c.get_period_key(START + timedelta(days=90)) == 1

    def test_march_31_is_window_1_not_window_0(self):
        c = make_cercas(aggregation_type=AggregationType.QUARTERLY)
        mar_31 = datetime(2024, 3, 31)   # day 90 from 2024-01-01
        assert c.get_period_key(mar_31) == 1, (
            "BUG (Annex 2.3.6): Mar 31 is day 90 → window 1; "
            "calendar-quarter grouping wrongly puts it in Q1 (window 0)"
        )


# ===========================================================================
# aggregate_changes — monthly (30-day windows)
# ===========================================================================

class TestAggregateChangesMonthly:

    def test_two_changes_within_first_30_days_form_one_bucket(self):
        c = make_cercas(aggregation_type=AggregationType.MONTHLY)
        changes = [
            (START + timedelta(days=1),  0.01),
            (START + timedelta(days=29), 0.02),
        ]
        result = c.aggregate_changes(changes)
        assert len(result) == 1
        assert abs(result[0] - 0.03) < EPS

    def test_change_on_day_30_creates_second_bucket(self):
        c = make_cercas(aggregation_type=AggregationType.MONTHLY)
        changes = [
            (START + timedelta(days=1),  0.01),
            (START + timedelta(days=29), 0.02),
            (START + timedelta(days=30), 0.03),
        ]
        result = c.aggregate_changes(changes)
        assert len(result) == 2

    def test_january_spans_two_30_day_windows(self):
        c = make_cercas(aggregation_type=AggregationType.MONTHLY)
        changes = [
            (datetime(2024, 1, 2),  0.01),   # day 1  → window 0
            (datetime(2024, 1, 30), 0.02),   # day 29 → window 0
            (datetime(2024, 1, 31), 0.03),   # day 30 → window 1 (still Jan!)
        ]
        result = c.aggregate_changes(changes)
        assert len(result) == 2, (
            "BUG (Annex 2.3.5): calendar-month grouping merges Jan 31 with Jan; "
            "day 30 must start a new 30-day window"
        )

    def test_three_30_day_windows_produce_three_buckets(self):
        c = make_cercas(aggregation_type=AggregationType.MONTHLY)
        changes = [
            (START + timedelta(days=5),  0.10),
            (START + timedelta(days=35), 0.20),
            (START + timedelta(days=65), 0.30),
        ]
        result = c.aggregate_changes(changes)
        assert len(result) == 3


# ===========================================================================
# aggregate_changes — quarterly (90-day windows)
# ===========================================================================

class TestAggregateChangesQuarterly:

    def test_changes_within_first_90_days_form_one_bucket(self):
        c = make_cercas(aggregation_type=AggregationType.QUARTERLY)
        changes = [
            (START + timedelta(days=1),  0.10),
            (START + timedelta(days=89), 0.05),
        ]
        result = c.aggregate_changes(changes)
        assert len(result) == 1
        assert abs(result[0] - 0.15) < EPS

    def test_change_on_day_90_creates_second_bucket(self):
        c = make_cercas(aggregation_type=AggregationType.QUARTERLY)
        changes = [
            (START + timedelta(days=89), 0.10),
            (START + timedelta(days=90), 0.05),
        ]
        result = c.aggregate_changes(changes)
        assert len(result) == 2

    def test_q1_spans_two_90_day_windows(self):
        c = make_cercas(aggregation_type=AggregationType.QUARTERLY)
        changes = [
            (datetime(2024, 3, 30), 0.10),   # day 89 → window 0
            (datetime(2024, 3, 31), 0.05),   # day 90 → window 1 (still Q1!)
        ]
        result = c.aggregate_changes(changes)
        assert len(result) == 2, (
            "BUG (Annex 2.3.6): calendar-quarter grouping merges Mar 31 into Q1; "
            "day 90 must start a new 90-day window"
        )


# ===========================================================================
# build_histogram — correctness
# ===========================================================================

class TestBuildHistogram:

    def test_histogram_length_equals_n_intervals(self):
        c = make_cercas(number_of_intervals=5)
        hist = c.build_histogram([0.1, 0.3, 0.5, 0.7, 0.9])
        assert len(hist) == 5

    def test_frequency_sum_equals_number_of_input_values(self):
        c = make_cercas(number_of_intervals=3)
        hist = c.build_histogram([0.1, 0.5, 0.9, 1.3, 1.7])
        assert sum(f for _, _, f in hist) == 5

    def test_bins_are_contiguous(self):
        c = make_cercas(number_of_intervals=4)
        hist = c.build_histogram([1.0, 2.0, 3.0, 4.0])
        for i in range(len(hist) - 1):
            assert hist[i][1] == pytest.approx(hist[i + 1][0])

    def test_single_value_goes_into_first_bin(self):
        c = make_cercas(number_of_intervals=3)
        hist = c.build_histogram([5.0])
        assert hist[0][2] == 1
        assert sum(f for _, _, f in hist) == 1

    def test_n_equals_1_puts_all_values_in_single_bin(self):
        c = make_cercas(number_of_intervals=1)
        hist = c.build_histogram([0.2, 0.5, 0.8])
        assert len(hist) == 1
        assert hist[0][2] == 3


# ===========================================================================
# run_analysis — end date derived from aggregation type
# ===========================================================================

class TestRunAnalysisEndDateDerived:

    @patch.object(CERCAS, "fetch_rates", side_effect=fake_fetch)
    def test_monthly_end_date_is_start_plus_29_days(self, _):
        c = make_cercas(aggregation_type=AggregationType.MONTHLY)
        c.run_analysis()
        assert c.end_date == START + timedelta(days=29)

    @patch.object(CERCAS, "fetch_rates", side_effect=fake_fetch)
    def test_quarterly_end_date_is_start_plus_89_days(self, _):
        c = make_cercas(aggregation_type=AggregationType.QUARTERLY)
        c.run_analysis()
        assert c.end_date == START + timedelta(days=89)

    @patch.object(CERCAS, "fetch_rates", side_effect=fake_fetch)
    def test_histogram_has_exactly_n_intervals(self, _):
        c = make_cercas(number_of_intervals=7)
        c.run_analysis()
        assert len(c.histogram) == 7

    @patch.object(CERCAS, "fetch_rates", side_effect=fake_fetch)
    def test_frequency_sum_equals_number_of_aggregated_windows(self, _):
        c = make_cercas(aggregation_type=AggregationType.MONTHLY, number_of_intervals=5)
        c.run_analysis()
        total_counts = sum(f for _, _, f in c.histogram)
        assert total_counts == 4


# ===========================================================================
# run_analysis — missing configuration
# ===========================================================================

class TestRunAnalysisMissingConfig:

    def test_no_base_currency_histogram_stays_none(self):
        c = make_cercas(base=None)
        c.run_analysis()
        assert c.histogram is None

    def test_no_quote_currency_histogram_stays_none(self):
        c = make_cercas(quote=None)
        c.run_analysis()
        assert c.histogram is None

    def test_no_start_date_histogram_stays_none(self):
        c = make_cercas(start_date=None)
        c.run_analysis()
        assert c.histogram is None

    def test_no_aggregation_type_histogram_stays_none(self):
        c = make_cercas(aggregation_type=None)
        c.run_analysis()
        assert c.histogram is None

    def test_no_intervals_histogram_stays_none(self):
        c = make_cercas(number_of_intervals=None)
        c.run_analysis()
        assert c.histogram is None

    def test_zero_intervals_histogram_stays_none(self):
        c = make_cercas(number_of_intervals=0)
        c.run_analysis()
        assert c.histogram is None


# ===========================================================================
# run_analysis — insufficient data
# ===========================================================================

class TestRunAnalysisInsufficientData:

    @patch.object(CERCAS, "fetch_rates", return_value=[(datetime(2024, 1, 2), 4.0)])
    def test_single_data_point_histogram_stays_none(self, _):
        c = make_cercas()
        c.run_analysis()
        assert c.histogram is None

    @patch.object(CERCAS, "fetch_rates", return_value=[])
    def test_empty_rates_histogram_stays_none(self, _):
        c = make_cercas()
        c.run_analysis()
        assert c.histogram is None


# ===========================================================================
# set_start — Annex 4.1.2
# ===========================================================================

class TestSetStart:

    def test_set_start_stores_start_date(self):
        c = CERCAS()
        c.set_start(datetime(2024, 3, 1))
        assert c.start_date == datetime(2024, 3, 1)

    def test_set_start_prints_success(self, capsys):
        c = CERCAS()
        c.set_start(datetime(2024, 3, 1))
        assert "successfully" in capsys.readouterr().out.lower()

    def test_set_start_rejects_date_before_2002_01_02(self, capsys):
        c = CERCAS()
        c.set_start(datetime(2002, 1, 1))
        assert c.start_date is None
        assert "error" in capsys.readouterr().out.lower()

    def test_set_start_accepts_2002_01_02_as_earliest_date(self):
        c = CERCAS()
        c.set_start(datetime(2002, 1, 2))
        assert c.start_date == datetime(2002, 1, 2)

    def test_set_start_rejects_future_date(self, capsys):
        c = CERCAS()
        c.set_start(datetime(2099, 6, 1))
        assert c.start_date is None
        assert "error" in capsys.readouterr().out.lower()

    def test_set_start_does_not_set_end_date(self):
        """end_date is no longer user-controlled (Annex: Req 2.6.3 removed)."""
        c = CERCAS()
        c.set_start(datetime(2024, 3, 1))
        assert c.end_date is None
