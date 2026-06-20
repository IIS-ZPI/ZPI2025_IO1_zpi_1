"""
Integration tests for the CERCASShell CLI (cmd.Cmd wrapper).

SRS sections covered:
    4.1.1  exit command
    4.1.2  set_pair command
    4.1.3  set_start command
    4.1.4  set_aggregation command
    4.1.5  run_analysis command
    4.1.6  export command
    4.1.7  show_config command
    4.1.8  switch_aggregation command

NOTE: shell.py imports from `src.app.core.*` instead of `core.*`.  This creates
a dual-module identity problem when tests also import from `core.*`.  The enum
comparison tests below therefore rely only on printed output to avoid false
failures caused by the import path mismatch.

KNOWN BUG (SRS 4.1.4): do_set_aggregation raises ValueError for an invalid
aggregation type argument instead of printing a user-friendly error message.
"""

import io
import os
import tempfile
from datetime import datetime
from unittest.mock import patch

from app.cli.shell import CERCASShell


# =============================================================================
# Helpers
# =============================================================================

def _run(shell: CERCASShell, command: str) -> str:
    """Run a single shell command and return captured stdout."""
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        shell.onecmd(command)
    return buf.getvalue()


# =============================================================================
# SRS 4.1.2 – set_pair
# =============================================================================

def test_412_shell_set_pair_accepts_valid_pair():
    shell = CERCASShell()
    with patch("app.core.cercas.validate_currency"):
        out = _run(shell, "set_pair EUR/USD")
    assert "successfully" in out.lower()


def test_412_shell_set_pair_stores_base_and_quote():
    shell = CERCASShell()
    with patch("app.core.cercas.validate_currency"):
        _run(shell, "set_pair EUR/USD")
    assert shell.app.base == "EUR"
    assert shell.app.quote == "USD"


def test_412_shell_set_pair_prints_usage_on_bad_format():
    shell = CERCASShell()
    out = _run(shell, "set_pair EURUSD")
    assert "usage" in out.lower()


def test_412_shell_set_pair_rejects_invalid_currency_code():
    shell = CERCASShell()
    out = _run(shell, "set_pair EU/USD")
    assert shell.app.base is None
    assert "error" in out.lower()


# =============================================================================
# SRS 4.1.3 – set_start
# =============================================================================

def test_413_shell_set_start_accepts_valid_date():
    shell = CERCASShell()
    out = _run(shell, "set_start 2023-01-01")
    assert "successfully" in out.lower()


def test_413_shell_set_start_stores_date():
    shell = CERCASShell()
    _run(shell, "set_start 2023-01-01")
    assert shell.app.start_date == datetime(2023, 1, 1)


def test_413_shell_set_start_prints_usage_on_bad_format():
    shell = CERCASShell()
    out = _run(shell, "set_start not-a-date")
    assert "usage" in out.lower()


def test_413_shell_set_start_rejects_date_before_nbp_epoch():
    shell = CERCASShell()
    out = _run(shell, "set_start 2001-12-31")
    assert shell.app.start_date is None
    assert "error" in out.lower()


def test_413_shell_set_start_rejects_future_date():
    shell = CERCASShell()
    out = _run(shell, "set_start 2099-01-01")
    assert shell.app.start_date is None
    assert "error" in out.lower()


# =============================================================================
# SRS 4.1.4 – set_aggregation
# =============================================================================

def test_414_shell_set_aggregation_monthly_prints_success():
    shell = CERCASShell()
    out = _run(shell, "set_aggregation MONTHLY")
    assert "successfully" in out.lower()


def test_414_shell_set_aggregation_quarterly_prints_success():
    shell = CERCASShell()
    out = _run(shell, "set_aggregation QUARTERLY")
    assert "successfully" in out.lower()


def test_414_shell_set_aggregation_accepts_lowercase_input():
    """Command should be case-insensitive per CLI convention."""
    shell = CERCASShell()
    out = _run(shell, "set_aggregation monthly")
    assert "successfully" in out.lower()


def test_414_shell_set_aggregation_invalid_prints_usage():
    shell = CERCASShell()
    out = _run(shell, "set_aggregation INVALID")
    assert "usage" in out.lower()


# =============================================================================
# SRS 4.1.5 – run_analysis
# =============================================================================

def test_415_shell_run_analysis_prints_error_when_pair_not_set():
    shell = CERCASShell()
    _run(shell, "set_start 2023-01-01")
    from app.core.aggregation_type import AggregationType as AT
    shell.app.aggregation_type = AT.MONTHLY
    shell.app.number_of_intervals = 5
    out = _run(shell, "run_analysis")
    assert "error" in out.lower()


def test_415_shell_run_analysis_prints_error_when_start_not_set():
    shell = CERCASShell()
    with patch("app.core.cercas.validate_currency"):
        _run(shell, "set_pair EUR/USD")
    from app.core.aggregation_type import AggregationType as AT
    shell.app.aggregation_type = AT.MONTHLY
    shell.app.number_of_intervals = 5
    out = _run(shell, "run_analysis")
    assert "error" in out.lower()


def test_415_shell_run_analysis_prints_error_when_aggregation_not_set():
    shell = CERCASShell()
    with patch("app.core.cercas.validate_currency"):
        _run(shell, "set_pair EUR/USD")
    _run(shell, "set_start 2023-01-01")
    shell.app.number_of_intervals = 5
    out = _run(shell, "run_analysis")
    assert "error" in out.lower()


def test_415_shell_run_analysis_prints_error_when_intervals_not_set():
    shell = CERCASShell()
    with patch("app.core.cercas.validate_currency"):
        _run(shell, "set_pair EUR/USD")
    _run(shell, "set_start 2023-01-01")
    from app.core.aggregation_type import AggregationType as AT
    shell.app.aggregation_type = AT.MONTHLY
    out = _run(shell, "run_analysis")
    assert "error" in out.lower()


# =============================================================================
# SRS 4.1.6 – export
# =============================================================================

def test_416_shell_export_prints_error_when_no_analysis_run():
    shell = CERCASShell()
    out = _run(shell, "export /tmp/out.csv")
    assert "error" in out.lower()


def test_416_shell_export_creates_csv_after_successful_analysis():
    shell = CERCASShell()
    shell.app.histogram = [(0.0, 0.5, 1), (0.5, 1.0, 2)]
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        tmp = f.name
    try:
        out = _run(shell, f"export {tmp}")
        assert "successfully" in out.lower()
        assert os.path.exists(tmp)
        with open(tmp) as f:
            content = f.read()
        assert "frequency" in content
    finally:
        os.unlink(tmp)


def test_416_shell_export_prints_error_on_non_csv_extension():
    shell = CERCASShell()
    shell.app.histogram = [(0.0, 0.5, 1)]
    out = _run(shell, "export output.txt")
    assert "error" in out.lower()


# =============================================================================
# SRS 4.1.7 – show_config
# =============================================================================

def test_417_shell_show_config_prints_not_set_for_empty_config():
    shell = CERCASShell()
    out = _run(shell, "show_config")
    assert "isn't set" in out.lower() or "not set" in out.lower()


def test_417_shell_show_config_shows_pair_when_set():
    shell = CERCASShell()
    with patch("app.core.cercas.validate_currency"):
        _run(shell, "set_pair EUR/USD")
    out = _run(shell, "show_config")
    assert "EUR" in out
    assert "USD" in out


def test_417_shell_show_config_shows_period_when_start_and_aggregation_set():
    shell = CERCASShell()
    _run(shell, "set_start 2023-01-01")
    _run(shell, "set_aggregation MONTHLY")
    out = _run(shell, "show_config")
    assert "2023-01-01" in out
    assert "2023-01-31" in out


def test_417_shell_show_config_shows_only_start_when_aggregation_missing():
    shell = CERCASShell()
    _run(shell, "set_start 2023-01-01")
    out = _run(shell, "show_config")
    assert "2023-01-01" in out
    assert "isn't set" in out.lower() or "not set" in out.lower()


# =============================================================================
# SRS 4.1.8 – switch_aggregation
# =============================================================================

def test_418_switch_aggregation_command_exists():
    shell = CERCASShell()
    assert hasattr(shell, "do_switch_aggregation"), (
        "BUG (SRS 4.1.8): CERCASShell is missing do_switch_aggregation method"
    )


def test_418_switch_aggregation_monthly_to_quarterly():
    shell = CERCASShell()
    _run(shell, "set_aggregation MONTHLY")
    out = _run(shell, "switch_aggregation")
    assert "quarterly" in out.lower()


def test_418_switch_aggregation_quarterly_to_monthly():
    shell = CERCASShell()
    _run(shell, "set_aggregation QUARTERLY")
    out = _run(shell, "switch_aggregation")
    assert "monthly" in out.lower()


def test_418_switch_aggregation_prints_error_when_not_set():
    shell = CERCASShell()
    out = _run(shell, "switch_aggregation")
    assert "error" in out.lower() or "must set" in out.lower()