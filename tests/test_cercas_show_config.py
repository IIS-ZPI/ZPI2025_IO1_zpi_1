"""
Unit tests for CERCAS.show_config().

SRS sections covered:
    4.1.7  show_config – display current analysis configuration
    2.5.1  System shall allow the user to view current settings
"""

import pytest
from unittest.mock import patch
from datetime import datetime

from core.cercas import CERCAS
from core.aggregation_type import AggregationType


# =============================================================================
# SRS 4.1.7 / 2.5.1 – show_config: currency pair
# =============================================================================

def test_417_show_config_reports_base_not_set_when_none(capsys):
    c = CERCAS()
    c.show_config()
    out = capsys.readouterr().out
    assert "isn't set" in out.lower() or "not set" in out.lower()


def test_417_show_config_reports_base_currency_when_set(capsys):
    c = CERCAS()
    with patch("core.cercas.validate_currency"):
        c.set_pair("EUR", "USD")
    capsys.readouterr()  # discard set_pair output
    c.show_config()
    out = capsys.readouterr().out
    assert "EUR" in out


def test_417_show_config_reports_quote_currency_when_set(capsys):
    c = CERCAS()
    with patch("core.cercas.validate_currency"):
        c.set_pair("EUR", "USD")
    capsys.readouterr()
    c.show_config()
    out = capsys.readouterr().out
    assert "USD" in out


def test_417_show_config_does_not_print_base_value_when_pair_not_set(capsys):
    c = CERCAS()
    c.show_config()
    out = capsys.readouterr().out
    assert "Base currency is:" not in out


# =============================================================================
# SRS 4.1.7 – show_config: period
# =============================================================================

def test_417_show_config_reports_dates_not_set_when_none(capsys):
    c = CERCAS()
    c.show_config()
    out = capsys.readouterr().out
    assert "isn't set" in out.lower() or "not set" in out.lower()


def test_417_show_config_reports_start_date_when_set(capsys):
    c = CERCAS()
    c.set_period(datetime(2023, 1, 1), datetime(2023, 3, 31))
    capsys.readouterr()
    c.show_config()
    out = capsys.readouterr().out
    assert "2023-01-01" in out


def test_417_show_config_reports_end_date_when_set(capsys):
    c = CERCAS()
    c.set_period(datetime(2023, 1, 1), datetime(2023, 3, 31))
    capsys.readouterr()
    c.show_config()
    out = capsys.readouterr().out
    assert "2023-03-31" in out


# =============================================================================
# SRS 4.1.7 – show_config: aggregation type
# =============================================================================

def test_417_show_config_reports_aggregation_not_set_when_none(capsys):
    c = CERCAS()
    c.show_config()
    out = capsys.readouterr().out
    assert "isn't set" in out.lower() or "not set" in out.lower()


def test_417_show_config_reports_monthly_when_set(capsys):
    c = CERCAS()
    c.set_type(AggregationType.MONTHLY)
    capsys.readouterr()
    c.show_config()
    out = capsys.readouterr().out
    assert "monthly" in out.lower()


def test_417_show_config_reports_quarterly_when_set(capsys):
    c = CERCAS()
    c.set_type(AggregationType.QUARTERLY)
    capsys.readouterr()
    c.show_config()
    out = capsys.readouterr().out
    assert "quarterly" in out.lower()


# =============================================================================
# SRS 4.1.7 – show_config: interval count
# =============================================================================

def test_417_show_config_reports_intervals_not_set_when_none(capsys):
    c = CERCAS()
    c.show_config()
    out = capsys.readouterr().out
    assert "isn't set" in out.lower() or "not set" in out.lower()


def test_417_show_config_reports_interval_count_when_set(capsys):
    c = CERCAS()
    c.set_interval(7)
    capsys.readouterr()
    c.show_config()
    out = capsys.readouterr().out
    assert "7" in out


def test_417_show_config_full_config_displays_all_fields(capsys):
    """When all fields are set, show_config must print all of them."""
    c = CERCAS()
    with patch("core.cercas.validate_currency"):
        c.set_pair("GBP", "PLN")
    c.set_period(datetime(2023, 6, 1), datetime(2023, 8, 31))
    c.set_type(AggregationType.QUARTERLY)
    c.set_interval(4)
    capsys.readouterr()

    c.show_config()
    out = capsys.readouterr().out

    assert "GBP" in out
    assert "PLN" in out
    assert "quarterly" in out.lower()
    assert "4" in out
