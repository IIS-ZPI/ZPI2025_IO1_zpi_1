"""
DANTE-style pytest reporter for the CERCAS test suite.

Replaces the default dot/F markers with numbered TEST lines and prints
a summary at the end.  Does NOT disable the built-in terminal reporter –
it just hooks into the report pipeline.
"""

import re
import pytest


# ---------------------------------------------------------------------------
# State shared across hooks
# ---------------------------------------------------------------------------
_results: list[dict] = []
_test_counter = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def _humanise(nodeid: str) -> str:
    """Convert a pytest node-id like 'tests/test_main.py::test_foo_bar'
    into a readable sentence 'foo bar'."""
    name = nodeid.split("::")[-1]
    if name.startswith("test_"):
        name = name[len("test_"):]
    return name.replace("_", " ")


def _extract_expected_got(report) -> tuple[str | None, str | None]:
    """Try to pull the Expected / Got values out of pytest's rewritten assert
    repr.  Returns (expected, got) strings, or (None, None) on failure."""
    try:
        lines = str(report.longrepr).splitlines()
        for line in lines:
            # Match patterns like:
            #   assert X == Y
            #   E   assert X == Y
            m = re.search(r"assert\s+(.+?)\s*==\s*(.+)", line)
            if m:
                got = m.group(1).strip()
                expected = m.group(2).strip()
                return expected, got
    except Exception:
        pass

    # Fallback: grab crash message
    try:
        msg = report.longrepr.reprcrash.message
        return msg, None
    except Exception:
        pass

    return None, None


# ---------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------

def pytest_sessionstart(session):
    print()
    print("=" * 60)
    print("  CERCAS – Currency Exchange Rate Change Analysis System")
    print("  Unit Test Suite")
    print("=" * 60)
    print()


def pytest_report_teststatus(report, config):
    """Suppress the default dot / F / E markers."""
    return ("", "", "")


def pytest_runtest_logreport(report):
    """Collect result after each test call phase."""
    global _test_counter

    # We only care about the 'call' phase (not setup/teardown)
    if report.when != "call":
        # But we do want to catch setup errors as failures
        if report.when == "setup" and report.failed:
            _test_counter += 1
            _results.append({
                "number": _test_counter,
                "name": _humanise(report.nodeid),
                "passed": False,
                "expected": None,
                "got": "Setup error",
            })
        return

    _test_counter += 1
    number = _test_counter

    if report.passed:
        _results.append({
            "number": number,
            "name": _humanise(report.nodeid),
            "passed": True,
            "expected": None,
            "got": None,
        })
        print(f"TEST {number}: Checking correctness of {_humanise(report.nodeid)}")
        print(f"Result: {GREEN}OK{RESET}")
        print()
    else:
        expected, got = _extract_expected_got(report)
        _results.append({
            "number": number,
            "name": _humanise(report.nodeid),
            "passed": False,
            "expected": expected,
            "got": got,
        })
        print(f"TEST {number}: Checking correctness of {_humanise(report.nodeid)}")
        print(f"Result: {RED}FAILED{RESET}")
        if expected is not None or got is not None:
            exp_str = expected if expected is not None else "?"
            got_str = got if got is not None else "?"
            print(f"  Expected: {exp_str}")
            print(f"  Got:      {got_str}")
        print()


def pytest_sessionfinish(session, exitstatus):
    total = len(_results)
    passed = sum(1 for r in _results if r["passed"])
    failed = total - passed

    print("=" * 60)
    print(
        f"SUMMARY: {total} test(s) run  |  "
        f"{GREEN}{passed} passed{RESET}  |  "
        f"{RED}{failed} failed{RESET}"
    )
    print("=" * 60)
    print()
