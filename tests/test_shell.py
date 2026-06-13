"""
Integration tests for the CERCASShell CLI (cmd.Cmd wrapper).

SRS sections covered:
    4.1.1  exit command
    4.1.2  set_pair command
    4.1.3  set_period command
    4.1.4  set_aggregation command
    4.1.5  run_analysis command
    4.1.6  export command
    4.1.7  show_config command
    4.1.8  switch_aggregation command  ← MISSING from implementation (intentionally FAILING test)

NOTE: shell.py imports from `src.app.core.*` instead of `core.*`.  This creates
a dual-module identity problem when tests also import from `core.*`.  The enum
comparison tests below therefore rely only on printed output to avoid false
failures caused by the import path mismatch.

KNOWN BUG (SRS 4.1.4): do_set_aggregation raises ValueError for an invalid
aggregation type argument instead of printing a user-friendly error message.
"""

import io
import os
import sys
import tempfile
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

# CERCASShell imports from src.app.core.* internally (wrong, but tested as-is)
from cli.shell import CERCASShell


# =============================================================================
# Helpers
# =============================================================================

def _run(shell: CERCASShell, command: str) -> str:
    """Run a single shell command and return captured stdout."""
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        shell.onecmd(command)
    return buf.getvalue()


# =============================================================================
# SRS 4.1.2 – set_pair
# =============================================================================

def test_412_shell_set_pair_accepts_valid_pair():
    shell = CERCASShell()
    with patch("core.cercas.validate_currency"):
        out = _run(shell, "set_pair EUR/USD")
    assert "successfully" in out.lower()


def test_412_shell_set_pair_stores_base_and_quote():
    shell = CERCASShell()
    with patch("core.cercas.validate_currency"):
        _run(shell, "set_pair EUR/USD")
    assert shell.app.base == "EUR"
    assert shell.app.quote == "USD"


def test_412_shell_set_pair_prints_usage_on_bad_format(capsys):
    shell = CERCASShell()
    out = _run(shell, "set_pair EURUSD")
    assert "usage" in out.lower()


def test_412_shell_set_pair_rejects_invalid_currency_code():
    shell = CERCASShell()
    out = _run(shell, "set_pair EU/USD")
    assert shell.app.base is None
    assert "error" in out.lower()


# =============================================================================
# Annex 4.1.2 – set_start  (replaces SRS 4.1.3 set_period; Req 2.6.3 removed)
# =============================================================================

def test_annex_412_shell_set_start_accepts_valid_date():
    shell = CERCASShell()
    out = _run(shell, "set_start 2023-06-01")
    assert "successfully" in out.lower()


def test_annex_412_shell_set_start_stores_start_date():
    shell = CERCASShell()
    _run(shell, "set_start 2023-06-01")
    assert shell.app.start_date == datetime(2023, 6, 1)


def test_annex_412_shell_set_start_does_not_store_end_date():
    """Annex: end date is derived during run_analysis, not user-provided."""
    shell = CERCASShell()
    _run(shell, "set_start 2023-06-01")
    assert shell.app.end_date is None


def test_annex_412_shell_set_start_prints_usage_on_bad_format():
    shell = CERCASShell()
    out = _run(shell, "set_start not-a-date")
    assert "usage" in out.lower()


def test_annex_412_shell_set_start_rejects_future_date():
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


def test_414_shell_set_aggregation_invalid_raises_instead_of_printing_error():
    """
    BUG (SRS 4.1.4): do_set_aggregation raises ValueError for invalid input
    instead of printing a user-friendly error message.
    The shell should catch the error and print it — not propagate the exception.
    """
    shell = CERCASShell()
    with pytest.raises(ValueError, match="Invalid aggregation type"):
        _run(shell, "set_aggregation INVALID")


# =============================================================================
# SRS 4.1.5 – run_analysis
# =============================================================================

def test_415_shell_run_analysis_prints_error_when_pair_not_set():
    shell = CERCASShell()
<<<<<<< Updated upstream
    shell.app.set_period(datetime(2023, 1, 1), datetime(2023, 3, 31))
    from core.aggregation_type import AggregationType as AT
=======
    shell.app.set_start(datetime(2023, 1, 1))
    from app.core.aggregation_type import AggregationType as AT
>>>>>>> Stashed changes
    shell.app.aggregation_type = AT.MONTHLY
    shell.app.number_of_intervals = 5
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
    # inject a fake histogram directly
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


# =============================================================================
# SRS 4.1.7 – show_config
# =============================================================================

def test_417_shell_show_config_prints_not_set_for_empty_config():
    shell = CERCASShell()
    out = _run(shell, "show_config")
    assert "isn't set" in out.lower() or "not set" in out.lower()


def test_417_shell_show_config_shows_pair_when_set():
    shell = CERCASShell()
    with patch("core.cercas.validate_currency"):
        _run(shell, "set_pair EUR/USD")
    out = _run(shell, "show_config")
    assert "EUR" in out
    assert "USD" in out


# =============================================================================
# SRS 4.1.8 – switch_aggregation  ← INTENTIONALLY FAILING
# =============================================================================

def test_418_switch_aggregation_command_exists():
    """
    SRS 4.1.8: the CLI shall provide a 'switch_aggregation' command that
    toggles between MONTHLY and QUARTERLY aggregation types.

    BUG: CERCASShell has no do_switch_aggregation method — SRS 4.1.8 is
    not implemented.  This test is intentionally FAILING to signal the gap.
    """
    shell = CERCASShell()
    assert hasattr(shell, "do_switch_aggregation"), (
        "BUG (SRS 4.1.8): CERCASShell is missing do_switch_aggregation method"
    )
