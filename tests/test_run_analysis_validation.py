"""
Unit tests for CERCAS.run_analysis() – pre-condition guards.

All expected behaviours derived from SRS v1.1.

SRS sections covered:
    4.1.5  run_analysis – execute analysis
    3.2    System shall validate all inputs before starting analysis
    2.3.1  System shall compute cross rates
    2.3.2  System shall compute daily changes
    2.3.3  System shall aggregate changes
    2.4.1  System shall build a histogram
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from core.cercas import CERCAS
from core.aggregation_type import AggregationType


# =============================================================================
# Helper – fully configured CERCAS instance (no real network calls)
# =============================================================================

def _configured(base="EUR", quote="USD") -> CERCAS:
    c = CERCAS()
    with patch("core.cercas.validate_currency"):
        c.set_pair(base, quote)
    c.set_period(datetime(2023, 1, 1), datetime(2023, 3, 31))
    c.set_type(AggregationType.MONTHLY)
    c.set_interval(5)
    return c


# =============================================================================
# SRS 3.2 – guard: missing currency pair
# =============================================================================

def test_32_run_analysis_fails_when_pair_not_set(capsys):
    c = CERCAS()
    c.set_period(datetime(2023, 1, 1), datetime(2023, 3, 31))
    c.set_type(AggregationType.MONTHLY)
    c.set_interval(5)
    c.run_analysis()
    assert "error" in capsys.readouterr().out.lower()


def test_32_run_analysis_does_not_set_histogram_when_pair_missing():
    c = CERCAS()
    c.set_period(datetime(2023, 1, 1), datetime(2023, 3, 31))
    c.set_type(AggregationType.MONTHLY)
    c.set_interval(5)
    c.run_analysis()
    assert c.histogram is None


# =============================================================================
# SRS 3.2 – guard: missing period
# =============================================================================

def test_32_run_analysis_fails_when_period_not_set(capsys):
    c = CERCAS()
    with patch("core.cercas.validate_currency"):
        c.set_pair("EUR", "USD")
    c.set_type(AggregationType.MONTHLY)
    c.set_interval(5)
    c.run_analysis()
    assert "error" in capsys.readouterr().out.lower()


def test_32_run_analysis_does_not_set_histogram_when_period_missing():
    c = CERCAS()
    with patch("core.cercas.validate_currency"):
        c.set_pair("EUR", "USD")
    c.set_type(AggregationType.MONTHLY)
    c.set_interval(5)
    c.run_analysis()
    assert c.histogram is None


# =============================================================================
# SRS 3.2 – guard: missing aggregation type
# =============================================================================

def test_32_run_analysis_fails_when_aggregation_not_set(capsys):
    c = CERCAS()
    with patch("core.cercas.validate_currency"):
        c.set_pair("EUR", "USD")
    c.set_period(datetime(2023, 1, 1), datetime(2023, 3, 31))
    c.set_interval(5)
    c.run_analysis()
    assert "error" in capsys.readouterr().out.lower()


# =============================================================================
# SRS 3.2 – guard: missing interval count
# =============================================================================

def test_32_run_analysis_fails_when_intervals_not_set(capsys):
    c = CERCAS()
    with patch("core.cercas.validate_currency"):
        c.set_pair("EUR", "USD")
    c.set_period(datetime(2023, 1, 1), datetime(2023, 3, 31))
    c.set_type(AggregationType.MONTHLY)
    c.run_analysis()
    assert "error" in capsys.readouterr().out.lower()


# =============================================================================
# SRS 4.1.5 – successful analysis path (mocked NBP)
# =============================================================================

_FAKE_RATES_EUR = [
    (datetime(2023, 1, 3), 4.68),
    (datetime(2023, 1, 4), 4.70),
    (datetime(2023, 1, 5), 4.71),
    (datetime(2023, 2, 1), 4.73),
    (datetime(2023, 2, 2), 4.72),
    (datetime(2023, 3, 1), 4.69),
    (datetime(2023, 3, 2), 4.65),
]

_FAKE_RATES_USD = [
    (datetime(2023, 1, 3), 4.31),
    (datetime(2023, 1, 4), 4.33),
    (datetime(2023, 1, 5), 4.34),
    (datetime(2023, 2, 1), 4.36),
    (datetime(2023, 2, 2), 4.35),
    (datetime(2023, 3, 1), 4.32),
    (datetime(2023, 3, 2), 4.28),
]


def test_415_run_analysis_prints_started_and_completed(capsys):
    c = _configured()
    with patch.object(c, "fetch_rates", side_effect=[_FAKE_RATES_EUR, _FAKE_RATES_USD]):
        c.run_analysis()
    out = capsys.readouterr().out
    assert "started" in out.lower()
    assert "completed" in out.lower()


def test_415_run_analysis_sets_histogram_on_success():
    c = _configured()
    with patch.object(c, "fetch_rates", side_effect=[_FAKE_RATES_EUR, _FAKE_RATES_USD]):
        c.run_analysis()
    assert c.histogram is not None


def test_415_run_analysis_histogram_has_correct_number_of_bins():
    c = _configured()
    with patch.object(c, "fetch_rates", side_effect=[_FAKE_RATES_EUR, _FAKE_RATES_USD]):
        c.run_analysis()
    assert len(c.histogram) == c.number_of_intervals


def test_415_run_analysis_fails_when_api_returns_insufficient_data(capsys):
    """SRS 3.2: at least 2 data points required to compute daily changes."""
    c = _configured()
    single_point = [(datetime(2023, 1, 3), 4.68)]
    with patch.object(c, "fetch_rates", side_effect=[single_point, single_point]):
        c.run_analysis()
    assert "error" in capsys.readouterr().out.lower()
    assert c.histogram is None


def test_415_run_analysis_with_pln_base_returns_empty_for_pln(capsys):
    """When base is PLN, fetch_rates("PLN") returns [] immediately (PLN is NBP base)."""
    c = _configured(base="PLN", quote="USD")
    assert c.fetch_rates("PLN") == []


def test_415_run_analysis_does_not_overwrite_histogram_on_failure():
    """If run_analysis fails, any previously successful histogram is preserved."""
    c = _configured()
    with patch.object(c, "fetch_rates", side_effect=[_FAKE_RATES_EUR, _FAKE_RATES_USD]):
        c.run_analysis()
    previous = c.histogram

    # now cause a failure
    with patch.object(c, "fetch_rates", side_effect=ValueError("API down")):
        c.run_analysis()

    assert c.histogram == previous
