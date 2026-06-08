from app.core import *

from src.app.core import currency_validator


# TESTS: is ISO4217 format 1
def test_is_iso4217_format_1():
    string = "PLN"
    assert currency_validator.is_iso4217_format(string) is True

# TESTS: is ISO4217 format 2
def test_is_iso4217_format_2():
    string = "PL"
    assert currency_validator.is_iso4217_format(string) is False

# TESTS: is ISO4217 format 3
def test_is_iso4217_format_3():
    string = "pln"
    assert currency_validator.is_iso4217_format(string) is False

# TESTS: is ISO4217 format 4
def test_is_iso4217_format_4():
    string = "PLNA"
    assert currency_validator.is_iso4217_format(string) is False

# TESTS: is ISO4217 format 5
def test_is_iso4217_format_5():
    string = "NLP"
    assert currency_validator.is_iso4217_format(string) is True

