import pytest
from datetime import datetime
from unittest.mock import patch
from app.core.aggregation_type import AggregationType
from app.core.cercas import CERCAS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

USD_RATES = [
    (datetime(2024, 1, 2), 4.00),
    (datetime(2024, 1, 3), 4.02),
    (datetime(2024, 2, 1), 4.05),
    (datetime(2024, 2, 2), 4.07),
    (datetime(2024, 3, 1), 4.10),
    (datetime(2024, 3, 4), 4.08),
]

EUR_RATES = [
    (datetime(2024, 1, 2), 4.30),
    (datetime(2024, 1, 3), 4.32),
    (datetime(2024, 2, 1), 4.35),
    (datetime(2024, 2, 2), 4.37),
    (datetime(2024, 3, 1), 4.40),
    (datetime(2024, 3, 4), 4.38),
]


def fake_fetch(currency):
    if currency == "USD":
        return USD_RATES
    if currency == "EUR":
        return EUR_RATES
    return []


def ready_cercas(**overrides) -> CERCAS:
    """Fully configured instance; override any field via kwargs."""
    c = CERCAS()
    c.base = overrides.get("base", "USD")
    c.quote = overrides.get("quote", "EUR")
    c.start_date = overrides.get("start_date", datetime(2024, 1, 2))
    c.end_date = overrides.get("end_date", datetime(2024, 3, 31))
    c.aggregation_type = overrides.get("aggregation_type", AggregationType.MONTHLY)
    c.number_of_intervals = overrides.get("number_of_intervals", 5)
    return c


# ---------------------------------------------------------------------------
# Missing configuration — histogram must stay None
# ---------------------------------------------------------------------------

class TestRunAnalysisMissingConfig:

    def test_no_base_currency(self):
        c = ready_cercas(base=None)
        c.run_analysis()
        assert c.histogram is None

    def test_no_quote_currency(self):
        c = ready_cercas(quote=None)
        c.run_analysis()
        assert c.histogram is None

    def test_no_start_date(self):
        c = ready_cercas(start_date=None)
        c.run_analysis()
        assert c.histogram is None

    def test_no_end_date(self):
        c = ready_cercas(end_date=None)
        c.run_analysis()
        assert c.histogram is None

    def test_no_aggregation_type(self):
        c = ready_cercas(aggregation_type=None)
        c.run_analysis()
        assert c.histogram is None

    def test_no_intervals(self):
        c = ready_cercas(number_of_intervals=None)
        c.run_analysis()
        assert c.histogram is None

    def test_zero_intervals(self):
        c = ready_cercas(number_of_intervals=0)
        c.run_analysis()
        assert c.histogram is None


# ---------------------------------------------------------------------------
# Successful run — histogram must be populated correctly
# ---------------------------------------------------------------------------

class TestRunAnalysisSuccess:

    @patch.object(CERCAS, "fetch_rates", side_effect=fake_fetch)
    def test_histogram_is_set_after_run(self, _):
        c = ready_cercas()
        c.run_analysis()
        assert c.histogram is not None

    @patch.object(CERCAS, "fetch_rates", side_effect=fake_fetch)
    def test_histogram_has_exactly_n_intervals(self, _):
        c = ready_cercas(number_of_intervals=5)
        c.run_analysis()
        assert len(c.histogram) == 5

    @patch.object(CERCAS, "fetch_rates", side_effect=fake_fetch)
    def test_histogram_interval_count_is_respected(self, _):
        """Interval count from config must be honoured, not approximated."""
        for n in (1, 3, 7, 10):
            c = ready_cercas(number_of_intervals=n)
            c.run_analysis()
            assert len(c.histogram) == n, f"Expected {n} bins, got {len(c.histogram)}"

    @patch.object(CERCAS, "fetch_rates", side_effect=fake_fetch)
    def test_rerun_overwrites_previous_histogram(self, _):
        c = ready_cercas(number_of_intervals=3)
        c.run_analysis()
        c.number_of_intervals = 7
        c.run_analysis()
        assert len(c.histogram) == 7


# ---------------------------------------------------------------------------
# Insufficient data — histogram must stay None
# ---------------------------------------------------------------------------

class TestRunAnalysisInsufficientData:

    @patch.object(CERCAS, "fetch_rates", return_value=[(datetime(2024, 1, 2), 4.0)])
    def test_single_data_point(self, _):
        c = ready_cercas()
        c.run_analysis()
        assert c.histogram is None

    @patch.object(CERCAS, "fetch_rates", return_value=[])
    def test_empty_rates(self, _):
        c = ready_cercas()
        c.run_analysis()
        assert c.histogram is None
