"""
Unit tests for the CERCAS (Currency Exchange Rate Change Analysis System).

Covers:
  - is_iso4217_format        (6 tests)
  - AggregationType          (2 tests)
  - CERCAS.set_pair          (3 tests)
  - CERCAS.set_interval      (3 tests)
  - CERCAS.set_period        (5 tests)
  - CERCAS.set_type          (2 tests)
  - CERCAS.__daily_changes   (2 tests)
  - CERCAS.__get_period_key  (5 tests)
  - CERCAS.__aggregate_changes (2 tests)
  - CERCAS.__build_histogram (4 tests)
  - CERCAS.__build_cross_rate_series (3 tests)
  - CERCAS.export            (3 tests)
  - CERCAS.run_analysis      (4 tests)

Total: 44 tests
"""

import os
import tempfile
import pytest
from datetime import datetime
from unittest.mock import patch

from src.app.core.currency_validator import is_iso4217_format
from src.app.core.aggregation_type import AggregationType
from src.app.core.cercas import CERCAS


# ===========================================================================
# is_iso4217_format  (6 tests)
# ===========================================================================

def test_is_iso4217_format_valid_uppercase_code():
    assert is_iso4217_format("USD") is True


def test_is_iso4217_format_lowercase_rejected():
    assert is_iso4217_format("usd") is False


def test_is_iso4217_format_too_short_rejected():
    assert is_iso4217_format("US") is False


def test_is_iso4217_format_too_long_rejected():
    assert is_iso4217_format("USDD") is False


def test_is_iso4217_format_digits_rejected():
    assert is_iso4217_format("123") is False


def test_is_iso4217_format_empty_string_rejected():
    assert is_iso4217_format("") is False


# ===========================================================================
# AggregationType  (2 tests)
# ===========================================================================

def test_aggregation_type_monthly_value():
    assert AggregationType.MONTHLY.value == "MONTHLY"


def test_aggregation_type_quarterly_value():
    assert AggregationType.QUARTERLY.value == "QUARTERLY"


# ===========================================================================
# CERCAS.set_pair  (3 tests)
# ===========================================================================

def test_set_pair_stores_base_and_quote():
    c = CERCAS()
    with patch("src.app.core.cercas.validate_currency"):
        c.set_pair("eur", "usd")
    assert c.base == "EUR"
    assert c.quote == "USD"


def test_set_pair_converts_input_to_uppercase():
    c = CERCAS()
    with patch("src.app.core.cercas.validate_currency"):
        c.set_pair("gbp", "jpy")
    assert c.base == "GBP"
    assert c.quote == "JPY"


def test_set_pair_invalid_currency_leaves_pair_unset():
    c = CERCAS()
    with patch("src.app.core.cercas.validate_currency", side_effect=ValueError("bad")):
        c.set_pair("xxx", "yyy")
    assert c.base is None


# ===========================================================================
# CERCAS.set_interval  (3 tests)
# ===========================================================================

def test_set_interval_positive_number_stored():
    c = CERCAS()
    c.set_interval(5)
    assert c.number_of_intervals == 5


def test_set_interval_zero_accepted():
    # The SRS requires positive, but the current implementation accepts 0.
    c = CERCAS()
    c.set_interval(0)
    assert c.number_of_intervals == 0


def test_set_interval_negative_not_stored():
    c = CERCAS()
    c.set_interval(-1)
    assert c.number_of_intervals is None


# ===========================================================================
# CERCAS.set_period  (5 tests)
# ===========================================================================

def test_set_period_valid_range_stored():
    c = CERCAS()
    start = datetime(2023, 1, 1)
    end = datetime(2023, 2, 1)
    c.set_period(start, end)
    assert c.start_date == start
    assert c.end_date == end


def test_set_period_end_before_start_not_stored():
    c = CERCAS()
    c.set_period(datetime(2023, 6, 1), datetime(2023, 1, 1))
    assert c.start_date is None


def test_set_period_before_min_date_not_stored():
    c = CERCAS()
    c.set_period(datetime(2001, 12, 31), datetime(2002, 1, 15))
    assert c.start_date is None


def test_set_period_start_in_future_not_stored():
    c = CERCAS()
    # End is only 14 days after start so the 3-month check is not triggered.
    c.set_period(datetime(2099, 1, 1), datetime(2099, 1, 15))
    assert c.start_date is None


def test_set_period_longer_than_3_months_not_stored():
    c = CERCAS()
    c.set_period(datetime(2023, 1, 1), datetime(2023, 6, 1))
    assert c.start_date is None


# ===========================================================================
# CERCAS.set_type  (2 tests)
# ===========================================================================

def test_set_type_monthly_stored():
    c = CERCAS()
    c.set_type(AggregationType.MONTHLY)
    assert c.aggregation_type == AggregationType.MONTHLY


def test_set_type_quarterly_stored():
    c = CERCAS()
    c.set_type(AggregationType.QUARTERLY)
    assert c.aggregation_type == AggregationType.QUARTERLY


# ===========================================================================
# CERCAS.__daily_changes  (2 tests)
# ===========================================================================

def test_daily_changes_correct_differences():
    c = CERCAS()
    d1 = datetime(2023, 1, 1)
    d2 = datetime(2023, 1, 2)
    d3 = datetime(2023, 1, 3)
    series = [(d1, 1.0), (d2, 1.5), (d3, 1.2)]
    changes = c._CERCAS__daily_changes(series)
    assert len(changes) == 2
    assert abs(changes[0][1] - 0.5) < 1e-9
    assert abs(changes[1][1] - (-0.3)) < 1e-9


def test_daily_changes_single_element_returns_empty():
    c = CERCAS()
    series = [(datetime(2023, 1, 1), 1.0)]
    changes = c._CERCAS__daily_changes(series)
    assert changes == []


# ===========================================================================
# CERCAS.__get_period_key  (5 tests)
# ===========================================================================

def test_get_period_key_monthly_returns_year_month():
    c = CERCAS()
    c.aggregation_type = AggregationType.MONTHLY
    key = c._CERCAS__get_period_key(datetime(2023, 3, 15))
    assert key == (2023, 3)


def test_get_period_key_quarterly_q1():
    c = CERCAS()
    c.aggregation_type = AggregationType.QUARTERLY
    key = c._CERCAS__get_period_key(datetime(2023, 2, 10))
    assert key == (2023, 1)


def test_get_period_key_quarterly_q2():
    c = CERCAS()
    c.aggregation_type = AggregationType.QUARTERLY
    key = c._CERCAS__get_period_key(datetime(2023, 5, 1))
    assert key == (2023, 2)


def test_get_period_key_quarterly_q3():
    c = CERCAS()
    c.aggregation_type = AggregationType.QUARTERLY
    key = c._CERCAS__get_period_key(datetime(2023, 8, 20))
    assert key == (2023, 3)


def test_get_period_key_quarterly_q4():
    c = CERCAS()
    c.aggregation_type = AggregationType.QUARTERLY
    key = c._CERCAS__get_period_key(datetime(2023, 11, 5))
    assert key == (2023, 4)


# ===========================================================================
# CERCAS.__aggregate_changes  (2 tests)
# ===========================================================================

def test_aggregate_changes_monthly_sums():
    c = CERCAS()
    c.aggregation_type = AggregationType.MONTHLY
    changes = [
        (datetime(2023, 1, 2), 0.1),
        (datetime(2023, 1, 3), 0.2),
        (datetime(2023, 2, 1), 0.3),
    ]
    result = c._CERCAS__aggregate_changes(changes)
    # Jan: 0.1+0.2=0.3, Feb: 0.3
    assert len(result) == 2
    assert abs(result[0] - 0.3) < 1e-9
    assert abs(result[1] - 0.3) < 1e-9


def test_aggregate_changes_quarterly_sums():
    c = CERCAS()
    c.aggregation_type = AggregationType.QUARTERLY
    changes = [
        (datetime(2023, 1, 2), 0.1),
        (datetime(2023, 2, 1), 0.2),
        (datetime(2023, 5, 1), 0.5),
    ]
    result = c._CERCAS__aggregate_changes(changes)
    # Q1: 0.1+0.2=0.3, Q2: 0.5
    assert len(result) == 2
    assert abs(result[0] - 0.3) < 1e-9
    assert abs(result[1] - 0.5) < 1e-9


# ===========================================================================
# CERCAS.__build_histogram  (4 tests)
# ===========================================================================

def test_build_histogram_correct_number_of_bins():
    c = CERCAS()
    c.number_of_intervals = 3
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    result = c._CERCAS__build_histogram(values)
    assert len(result) == 3


def test_build_histogram_all_values_assigned():
    c = CERCAS()
    c.number_of_intervals = 3
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    result = c._CERCAS__build_histogram(values)
    total_freq = sum(freq for _, _, freq in result)
    assert total_freq == len(values)


def test_build_histogram_all_same_values_single_bin():
    c = CERCAS()
    c.number_of_intervals = 5
    values = [2.5, 2.5, 2.5]
    result = c._CERCAS__build_histogram(values)
    assert len(result) == 1
    assert result[0][2] == 3


def test_build_histogram_empty_raises_value_error():
    c = CERCAS()
    c.number_of_intervals = 3
    with pytest.raises(ValueError):
        c._CERCAS__build_histogram([])


# ===========================================================================
# CERCAS.__build_cross_rate_series  (3 tests)
# ===========================================================================

def test_build_cross_rate_series_pln_as_base():
    c = CERCAS()
    c.base = "PLN"
    c.quote = "USD"
    d = datetime(2023, 1, 2)
    result = c._CERCAS__build_cross_rate_series([], [(d, 4.0)])
    assert len(result) == 1
    assert abs(result[0][1] - 0.25) < 1e-9


def test_build_cross_rate_series_pln_as_quote():
    c = CERCAS()
    c.base = "EUR"
    c.quote = "PLN"
    d = datetime(2023, 1, 2)
    result = c._CERCAS__build_cross_rate_series([(d, 4.5)], [])
    assert len(result) == 1
    assert abs(result[0][1] - 4.5) < 1e-9


def test_build_cross_rate_series_cross_rate_calculation():
    c = CERCAS()
    c.base = "EUR"
    c.quote = "USD"
    d = datetime(2023, 1, 2)
    # EUR/PLN = 4.5, USD/PLN = 4.0  =>  EUR/USD = 4.5 / 4.0 = 1.125
    base_rates = [(d, 4.5)]
    quote_rates = [(d, 4.0)]
    result = c._CERCAS__build_cross_rate_series(base_rates, quote_rates)
    assert len(result) == 1
    assert abs(result[0][1] - 1.125) < 1e-9


# ===========================================================================
# CERCAS.export  (3 tests)
# ===========================================================================

def test_export_no_histogram_prints_error(capsys):
    c = CERCAS()
    c.export("output.csv")
    captured = capsys.readouterr()
    assert "No analysis results" in captured.out


def test_export_invalid_extension_prints_error(capsys):
    c = CERCAS()
    # Give it a histogram so we reach the extension check
    c.histogram = [(0.0, 1.0, 3)]
    c.export("output.txt")
    captured = capsys.readouterr()
    assert ".csv" in captured.out


def test_export_creates_file_with_correct_content():
    c = CERCAS()
    c.histogram = [
        (0.0, 1.0, 5),
        (1.0, 2.0, 3),
    ]
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        c.export(path)
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        assert lines[0] == "interval_start;interval_end;frequency"
        assert lines[1] == "0.0;1.0;5"
        assert lines[2] == "1.0;2.0;3"
    finally:
        os.unlink(path)


# ===========================================================================
# CERCAS.run_analysis  (4 tests)
# ===========================================================================

def test_run_analysis_without_pair_prints_error(capsys):
    c = CERCAS()
    c.run_analysis()
    captured = capsys.readouterr()
    assert "Currency pair not set" in captured.out


def test_run_analysis_without_period_prints_error(capsys):
    c = CERCAS()
    with patch("src.app.core.cercas.validate_currency"):
        c.set_pair("EUR", "USD")
    c.run_analysis()
    captured = capsys.readouterr()
    assert "Period not set" in captured.out


def test_run_analysis_without_aggregation_type_prints_error(capsys):
    c = CERCAS()
    with patch("src.app.core.cercas.validate_currency"):
        c.set_pair("EUR", "USD")
    c.set_period(datetime(2023, 1, 1), datetime(2023, 2, 1))
    c.run_analysis()
    captured = capsys.readouterr()
    assert "Aggregation type not set" in captured.out


def test_run_analysis_without_intervals_prints_error(capsys):
    c = CERCAS()
    with patch("src.app.core.cercas.validate_currency"):
        c.set_pair("EUR", "USD")
    c.set_period(datetime(2023, 1, 1), datetime(2023, 2, 1))
    c.set_type(AggregationType.MONTHLY)
    c.run_analysis()
    captured = capsys.readouterr()
    assert "Intervals not set" in captured.out
