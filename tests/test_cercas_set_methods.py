"""
Unit tests for CERCAS configuration methods.

All expected behaviours derived directly from SRS v1.1.

SRS sections covered:
    2.1.1  set_pair     – currency pair in ISO 4217
    2.1.2  set_start    – analysis start date in yyyy-mm-dd
    2.1.3  set_type     – aggregation level (monthly / quarterly)
    2.1.4  set_interval – number of intervals
    2.2.5  Dates not earlier than 2002-01-02
    2.6.1  Currency code validation
    2.6.5  Interval count must be a positive integer
"""

import pytest
from datetime import datetime
from unittest.mock import patch

from app.core.cercas import CERCAS
from app.core.aggregation_type import AggregationType

EPS = 1e-9


# =============================================================================
# SRS 2.1.1 / 2.6.1 – set_pair
# =============================================================================

def test_211_set_pair_stores_base_and_quote():
    c = CERCAS()
    with patch("app.core.cercas.validate_currency"):
        c.set_pair("EUR", "USD")
    assert c.base == "EUR"
    assert c.quote == "USD"


def test_211_set_pair_converts_lowercase_input_to_uppercase():
    c = CERCAS()
    with patch("app.core.cercas.validate_currency"):
        c.set_pair("eur", "usd")
    assert c.base == "EUR"
    assert c.quote == "USD"


def test_211_set_pair_prints_success_message(capsys):
    c = CERCAS()
    with patch("app.core.cercas.validate_currency"):
        c.set_pair("EUR", "USD")
    assert "successfully" in capsys.readouterr().out.lower()


def test_261_set_pair_rejects_too_short_currency_code(capsys):
    """SRS 2.6.1: currency codes must be ISO 4217 (3 uppercase letters)."""
    c = CERCAS()
    c.set_pair("EU", "USD")
    assert c.base is None
    assert "error" in capsys.readouterr().out.lower()


def test_261_set_pair_rejects_too_long_currency_code(capsys):
    c = CERCAS()
    c.set_pair("EURO", "USD")
    assert c.base is None
    assert "error" in capsys.readouterr().out.lower()


def test_261_set_pair_rejects_currency_not_in_nbp(capsys):
    """SRS 2.2.6: only currencies in NBP table are accepted."""
    c = CERCAS()
    with patch("app.core.cercas.validate_currency", side_effect=ValueError("Not supported by NBP")):
        c.set_pair("XYZ", "USD")
    assert c.base is None
    assert "error" in capsys.readouterr().out.lower()


def test_261_set_pair_does_not_partially_set_on_invalid_quote(capsys):
    """If the quote currency is invalid, neither base nor quote should be stored."""
    c = CERCAS()

    def fake_validate(code):
        if code == "INVALID":
            raise ValueError("Not supported")

    with patch("app.core.cercas.validate_currency", side_effect=fake_validate):
        c.set_pair("EUR", "INVALID")
    assert c.base is None
    assert c.quote is None


# =============================================================================
# SRS 2.1.2 / 2.2.5 – set_start
# =============================================================================

def test_212_set_start_stores_start_date():
    c = CERCAS()
    start = datetime(2023, 1, 1)
    c.set_start(start)
    assert c.start_date == start


def test_212_set_start_prints_success_message(capsys):
    c = CERCAS()
    c.set_start(datetime(2023, 1, 1))
    assert "successfully" in capsys.readouterr().out.lower()


def test_225_set_start_rejects_date_before_2002_01_02(capsys):
    """SRS 2.2.5: dates earlier than 2002-01-02 are not allowed."""
    c = CERCAS()
    c.set_start(datetime(2002, 1, 1))
    assert c.start_date is None
    assert "error" in capsys.readouterr().out.lower()


def test_225_set_start_accepts_date_on_2002_01_02():
    """SRS 2.2.5: 2002-01-02 is the earliest allowed start date."""
    c = CERCAS()
    c.set_start(datetime(2002, 1, 2))
    assert c.start_date == datetime(2002, 1, 2)


def test_212_set_start_rejects_future_date(capsys):
    c = CERCAS()
    c.set_start(datetime(2099, 1, 1))
    assert c.start_date is None
    assert "error" in capsys.readouterr().out.lower()


def test_212_end_date_derived_as_start_plus_30_days_for_monthly():
    """
    End date is not stored — it is derived dynamically.
    MONTHLY: start(2023-01-01) + 30 days = 2023-01-31.
    """
    c = CERCAS()
    c.set_start(datetime(2023, 1, 1))
    c.set_type(AggregationType.MONTHLY)
    end = c._CERCAS__get_end_date()
    assert end == datetime(2023, 1, 31)


def test_212_end_date_derived_as_start_plus_90_days_for_quarterly():
    """
    End date is not stored — it is derived dynamically.
    QUARTERLY: start(2023-01-01) + 90 days = 2023-04-01.
    """
    c = CERCAS()
    c.set_start(datetime(2023, 1, 1))
    c.set_type(AggregationType.QUARTERLY)
    end = c._CERCAS__get_end_date()
    assert end == datetime(2023, 4, 1)


# =============================================================================
# SRS 2.1.3 – set_type
# =============================================================================

def test_213_set_type_stores_monthly():
    c = CERCAS()
    c.set_type(AggregationType.MONTHLY)
    assert c.aggregation_type == AggregationType.MONTHLY


def test_213_set_type_stores_quarterly():
    c = CERCAS()
    c.set_type(AggregationType.QUARTERLY)
    assert c.aggregation_type == AggregationType.QUARTERLY


def test_213_set_type_prints_success_message(capsys):
    c = CERCAS()
    c.set_type(AggregationType.MONTHLY)
    assert "successfully" in capsys.readouterr().out.lower()


def test_213_set_type_can_switch_from_monthly_to_quarterly():
    """SRS 2.5.2: system shall allow switching between aggregation types."""
    c = CERCAS()
    c.set_type(AggregationType.MONTHLY)
    c.set_type(AggregationType.QUARTERLY)
    assert c.aggregation_type == AggregationType.QUARTERLY


# =============================================================================
# SRS 2.1.4 / 2.6.5 – set_interval
# =============================================================================

def test_214_set_interval_stores_positive_integer():
    c = CERCAS()
    c.set_interval(5)
    assert c.number_of_intervals == 5


def test_214_set_interval_stores_value_of_1():
    c = CERCAS()
    c.set_interval(1)
    assert c.number_of_intervals == 1


def test_214_set_interval_prints_success_message(capsys):
    c = CERCAS()
    c.set_interval(3)
    assert "successfully" in capsys.readouterr().out.lower()


def test_265_set_interval_rejects_negative_number(capsys):
    """SRS 2.6.5: interval count must be a positive integer."""
    c = CERCAS()
    c.set_interval(-1)
    assert c.number_of_intervals is None
    assert "error" in capsys.readouterr().out.lower()


def test_265_set_interval_rejects_zero(capsys):
    """
    SRS 2.6.5: interval count must be a POSITIVE integer.
    Zero is not positive.
    BUG: current code uses `number >= 0` which wrongly accepts 0.
    """
    c = CERCAS()
    c.set_interval(0)
    assert c.number_of_intervals is None, (
        "BUG (SRS 2.6.5): set_interval(0) was accepted — zero is not a positive integer"
    )