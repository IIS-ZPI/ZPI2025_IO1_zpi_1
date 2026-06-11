"""
Unit tests for currency_validator module.

SRS sections covered:
    2.6.1  Currency code must be ISO 4217 (3 uppercase letters)
    2.2.6  Only currencies listed in NBP tables are accepted
    2.2.6  PLN is always valid (NBP base currency)
"""

import pytest
from unittest.mock import patch

from core import currency_validator


# =============================================================================
# SRS 2.6.1 – is_iso4217_format
# =============================================================================

def test_is_iso4217_format_1():
    assert currency_validator.is_iso4217_format("PLN") is True


def test_is_iso4217_format_2():
    assert currency_validator.is_iso4217_format("PL") is False


def test_is_iso4217_format_3():
    assert currency_validator.is_iso4217_format("pln") is False


def test_is_iso4217_format_4():
    assert currency_validator.is_iso4217_format("PLNA") is False


def test_is_iso4217_format_5():
    assert currency_validator.is_iso4217_format("NLP") is True


def test_is_iso4217_format_digits_rejected():
    assert currency_validator.is_iso4217_format("US1") is False


def test_is_iso4217_format_empty_string_rejected():
    assert currency_validator.is_iso4217_format("") is False


def test_is_iso4217_format_special_chars_rejected():
    assert currency_validator.is_iso4217_format("EU€") is False


# =============================================================================
# SRS 2.2.6 – validate_currency (with mocked NBP API)
# =============================================================================

_FAKE_NBP_CODES = {"EUR", "USD", "GBP", "CHF", "JPY"}


def test_226_validate_currency_accepts_code_in_nbp_table():
    with patch.object(currency_validator, "fetch_all_nbp_codes", return_value=_FAKE_NBP_CODES):
        currency_validator.validate_currency("EUR")  # must not raise


def test_226_validate_currency_raises_for_code_not_in_nbp():
    with patch.object(currency_validator, "fetch_all_nbp_codes", return_value=_FAKE_NBP_CODES):
        with pytest.raises(ValueError, match="not supported by NBP"):
            currency_validator.validate_currency("XYZ")


def test_226_validate_currency_accepts_pln_without_api_call():
    """PLN is the NBP base currency and must always be valid."""
    with patch.object(currency_validator, "fetch_all_nbp_codes", return_value={"PLN"}):
        currency_validator.validate_currency("PLN")  # must not raise


def test_261_validate_currency_raises_for_bad_format_before_api_check():
    """SRS 2.6.1: format is validated before hitting the NBP API."""
    call_tracker = []
    with patch.object(currency_validator, "fetch_all_nbp_codes",
                      side_effect=lambda: call_tracker.append(1) or _FAKE_NBP_CODES):
        with pytest.raises(ValueError):
            currency_validator.validate_currency("EU")
    assert len(call_tracker) == 0, (
        "fetch_all_nbp_codes was called even though the code had wrong format — "
        "format check should short-circuit before the API call"
    )


def test_226_validate_currency_raises_for_lowercase_code():
    """validate_currency must reject lowercase codes (not ISO 4217 uppercase)."""
    with patch.object(currency_validator, "fetch_all_nbp_codes", return_value=_FAKE_NBP_CODES):
        with pytest.raises(ValueError):
            currency_validator.validate_currency("eur")

