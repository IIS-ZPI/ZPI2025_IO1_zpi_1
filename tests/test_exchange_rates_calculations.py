"""
Unit tests for CERCAS calculation logic.

Real NBP data used as fixtures (EUR/PLN and USD/PLN, 2024-01-02 → 2024-02-01).
No API calls are made during these tests.

Curl commands used to obtain fixture data:
    curl "https://api.nbp.pl/api/exchangerates/rates/A/eur/2024-01-02/2024-02-01/?format=json"
    curl "https://api.nbp.pl/api/exchangerates/rates/A/usd/2024-01-02/2024-02-01/?format=json"
"""

import pytest
from datetime import datetime

from app.core.aggregation_type import AggregationType
from app.core.cercas import CERCAS


# =============================================================================
# Fixtures
# =============================================================================

EUR_RATES_RAW = [
    ("2024-01-02", 4.3434), ("2024-01-03", 4.3646), ("2024-01-04", 4.3525),
    ("2024-01-05", 4.3484), ("2024-01-08", 4.3548), ("2024-01-09", 4.3351),
    ("2024-01-10", 4.3413), ("2024-01-11", 4.3505), ("2024-01-12", 4.3574),
    ("2024-01-15", 4.3748), ("2024-01-16", 4.3934), ("2024-01-17", 4.3978),
    ("2024-01-18", 4.4016), ("2024-01-19", 4.3846), ("2024-01-22", 4.3560),
    ("2024-01-23", 4.3697), ("2024-01-24", 4.3755), ("2024-01-25", 4.3790),
    ("2024-01-26", 4.3802), ("2024-01-29", 4.3653), ("2024-01-30", 4.3634),
    ("2024-01-31", 4.3434), ("2024-02-01", 4.3247),
]

USD_RATES_RAW = [
    ("2024-01-02", 3.9432), ("2024-01-03", 3.9909), ("2024-01-04", 3.9684),
    ("2024-01-05", 3.9850), ("2024-01-08", 3.9812), ("2024-01-09", 3.9612),
    ("2024-01-10", 3.9656), ("2024-01-11", 3.9680), ("2024-01-12", 3.9746),
    ("2024-01-15", 3.9963), ("2024-01-16", 4.0358), ("2024-01-17", 4.0434),
    ("2024-01-18", 4.0437), ("2024-01-19", 4.0289), ("2024-01-22", 3.9972),
    ("2024-01-23", 4.0133), ("2024-01-24", 4.0131), ("2024-01-25", 4.0189),
    ("2024-01-26", 4.0393), ("2024-01-29", 4.0326), ("2024-01-30", 4.0301),
    ("2024-01-31", 4.0135), ("2024-02-01", 4.0047),
]


def _to_rates(raw):
    return [(datetime.strptime(d, "%Y-%m-%d"), v) for d, v in raw]


@pytest.fixture
def eur_rates():
    return _to_rates(EUR_RATES_RAW)


@pytest.fixture
def usd_rates():
    return _to_rates(USD_RATES_RAW)


@pytest.fixture
def cercas():
    c = CERCAS()
    c.base = "EUR"
    c.quote = "USD"
    c.start_date = datetime(2024, 1, 2)
    c.aggregation_type = AggregationType.MONTHLY
    c.number_of_intervals = 5
    return c


@pytest.fixture
def eur_usd_series(cercas, eur_rates, usd_rates):
    return cercas.build_cross_rate_series(eur_rates, usd_rates)


@pytest.fixture
def eur_usd_changes(cercas, eur_usd_series):
    return cercas.compute_daily_changes(eur_usd_series)


# =============================================================================
# build_cross_rate_series
# =============================================================================

def test_cross_rate_eur_usd_series_length(cercas, eur_rates, usd_rates):
    """All 23 dates are common in both series."""
    series = cercas.build_cross_rate_series(eur_rates, usd_rates)
    assert len(series) == 23


def test_cross_rate_eur_usd_first_value(cercas, eur_rates, usd_rates):
    """2024-01-02: EUR/PLN=4.3434, USD/PLN=3.9432 → EUR/USD=4.3434/3.9432."""
    series = cercas.build_cross_rate_series(eur_rates, usd_rates)
    assert series[0][1] == pytest.approx(4.3434 / 3.9432, rel=1e-8)


def test_cross_rate_eur_usd_last_value(cercas, eur_rates, usd_rates):
    """2024-02-01: EUR/PLN=4.3247, USD/PLN=4.0047 → EUR/USD=4.3247/4.0047."""
    series = cercas.build_cross_rate_series(eur_rates, usd_rates)
    assert series[-1][1] == pytest.approx(4.3247 / 4.0047, rel=1e-8)


def test_cross_rate_eur_pln_direct(eur_rates, usd_rates):
    """quote=PLN → series equals EUR/PLN rates directly from NBP."""
    c = CERCAS()
    c.base = "EUR"
    c.quote = "PLN"
    series = c.build_cross_rate_series(eur_rates, [])
    assert len(series) == 23
    assert series[0][1] == pytest.approx(4.3434, rel=1e-6)
    assert series[-1][1] == pytest.approx(4.3247, rel=1e-6)


def test_cross_rate_pln_usd_inverse(eur_rates, usd_rates):
    """base=PLN → series equals 1/USD/PLN."""
    c = CERCAS()
    c.base = "PLN"
    c.quote = "USD"
    series = c.build_cross_rate_series([], usd_rates)
    assert len(series) == 23
    assert series[0][1] == pytest.approx(1.0 / 3.9432, rel=1e-8)
    assert series[-1][1] == pytest.approx(1.0 / 4.0047, rel=1e-8)


def test_cross_rate_partial_date_overlap(cercas, eur_rates, usd_rates):
    """Only intersection of dates is returned when inputs differ."""
    series = cercas.build_cross_rate_series(eur_rates[:5], usd_rates[:3])
    assert len(series) == 3


def test_cross_rate_dates_are_sorted(cercas, eur_usd_series):
    dates = [d for d, _ in eur_usd_series]
    assert dates == sorted(dates)


# =============================================================================
# compute_daily_changes
# =============================================================================

def test_daily_changes_count(eur_usd_changes):
    """22 changes for 23 data points."""
    assert len(eur_usd_changes) == 22


def test_daily_changes_first_value(cercas, eur_usd_series, eur_usd_changes):
    """First change: series[1] - series[0]."""
    expected = eur_usd_series[1][1] - eur_usd_series[0][1]
    assert eur_usd_changes[0] == pytest.approx(expected, rel=1e-8)


def test_daily_changes_last_value(cercas, eur_usd_series, eur_usd_changes):
    """Last change: series[-1] - series[-2]."""
    expected = eur_usd_series[-1][1] - eur_usd_series[-2][1]
    assert eur_usd_changes[-1] == pytest.approx(expected, rel=1e-8)


def test_daily_changes_first_value_from_raw(eur_usd_changes):
    """2024-01-03 minus 2024-01-02, computed from raw NBP rates."""
    expected = (4.3646 / 3.9909) - (4.3434 / 3.9432)
    assert eur_usd_changes[0] == pytest.approx(expected, rel=1e-8)


def test_daily_changes_last_value_from_raw(eur_usd_changes):
    """2024-02-01 minus 2024-01-31, computed from raw NBP rates."""
    expected = (4.3247 / 4.0047) - (4.3434 / 4.0135)
    assert eur_usd_changes[-1] == pytest.approx(expected, rel=1e-8)


def test_daily_changes_single_point_returns_empty(cercas, eur_usd_series):
    assert cercas.compute_daily_changes(eur_usd_series[:1]) == []


# =============================================================================
# build_histogram
# =============================================================================

def test_histogram_bin_count(cercas, eur_usd_changes):
    hist = cercas.build_histogram(eur_usd_changes)
    assert len(hist) == 5


def test_histogram_frequencies_sum_to_change_count(cercas, eur_usd_changes):
    """Every daily change must land in exactly one bin."""
    hist = cercas.build_histogram(eur_usd_changes)
    assert sum(f for _, _, f in hist) == len(eur_usd_changes)


def test_histogram_known_frequencies(cercas, eur_usd_changes):
    """
    Verified manually from NBP data (intervals=5):
      min = -0.0078531482,  max = 0.0031516116,  step = 0.0022009520
      bin[0] [-0.00785, -0.00565] → 2
      bin[1] [-0.00565, -0.00345] → 2
      bin[2] [-0.00345, -0.00125] → 3
      bin[3] [-0.00125,  0.00095] → 10
      bin[4] [ 0.00095,  0.00315] → 5
    """
    hist = cercas.build_histogram(eur_usd_changes)
    assert [f for _, _, f in hist] == [2, 2, 3, 10, 5]


def test_histogram_first_bin_starts_at_min(cercas, eur_usd_changes):
    hist = cercas.build_histogram(eur_usd_changes)
    assert hist[0][0] == pytest.approx(min(eur_usd_changes), rel=1e-10)


def test_histogram_last_bin_ends_at_max(cercas, eur_usd_changes):
    hist = cercas.build_histogram(eur_usd_changes)
    assert hist[-1][1] == pytest.approx(max(eur_usd_changes), rel=1e-10)


def test_histogram_bins_are_contiguous(cercas, eur_usd_changes):
    """End of bin[i] must equal start of bin[i+1]."""
    hist = cercas.build_histogram(eur_usd_changes)
    for i in range(len(hist) - 1):
        assert hist[i][1] == pytest.approx(hist[i + 1][0], rel=1e-10)


def test_histogram_different_interval_count(cercas, eur_usd_changes):
    cercas.number_of_intervals = 10
    hist = cercas.build_histogram(eur_usd_changes)
    assert len(hist) == 10
    assert sum(f for _, _, f in hist) == len(eur_usd_changes)


def test_histogram_empty_input_raises(cercas):
    with pytest.raises(ValueError):
        cercas.build_histogram([])


def test_histogram_all_identical_values_raises(cercas):
    with pytest.raises(ValueError):
        cercas.build_histogram([0.005] * 10)