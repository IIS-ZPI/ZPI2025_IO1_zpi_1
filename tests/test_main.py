"""
Unit tests for CERCAS – Currency Exchange Rate Change Analysis System.

All tests are derived directly from the Software Requirements Specification (SRS) v1.1.
Every expected value is computed manually according to the formulas defined in the SRS,
NOT inferred from the source code.

SRS sections covered:
    2.3.1  Cross-rate:   cross_rate = base_PLN_rate / quote_PLN_rate
    2.3.2  Daily change: change[d] = rate[d] - rate[d-1]
    2.3.4  Histogram:    N equal-width bins over [min, max] of daily changes
    2.4.1  Export to CSV file
    2.4.2  Output file must use ".csv" extension
    2.4.3  CSV header:   interval_start;interval_end;frequency
"""

import os
import tempfile
from datetime import datetime
from unittest.mock import patch

from app.core.cercas import CERCAS
from app.core.aggregation_type import AggregationType

EPS = 1e-9  # tolerance for floating-point comparisons


# =============================================================================
# SRS 2.3.1 – Cross-rate calculation
# "For currency pairs not directly quoted in PLN, the system shall first
#  calculate the daily cross-rate by dividing their respective PLN rates
#  retrieved from the API."
# =============================================================================

def test_231_cross_rate_is_base_pln_divided_by_quote_pln():
    """
    Manual calculation:
        EUR/PLN = 4.40,  USD/PLN = 2.20
        EUR/USD = 4.40 / 2.20 = 2.00  (exact)
    """
    c = CERCAS()
    c.base = "EUR"
    c.quote = "USD"
    d = datetime(2023, 1, 2)
    result = c.build_cross_rate_series([(d, 4.40)], [(d, 2.20)])
    assert len(result) == 1
    assert abs(result[0][1] - 2.00) < EPS


def test_231_each_date_cross_rate_computed_independently():
    """
    Manual calculation (EUR/PLN / USD/PLN per date):
        Date 1: 4.00 / 2.00 = 2.00
        Date 2: 5.00 / 2.50 = 2.00
        Date 3: 6.00 / 3.00 = 2.00
    All three must equal 2.00 independently.
    """
    c = CERCAS()
    c.base = "EUR"
    c.quote = "USD"
    dates = [datetime(2023, 1, d) for d in (2, 3, 4)]
    base_rates  = [(dates[0], 4.00), (dates[1], 5.00), (dates[2], 6.00)]
    quote_rates = [(dates[0], 2.00), (dates[1], 2.50), (dates[2], 3.00)]
    result = c.build_cross_rate_series(base_rates, quote_rates)
    assert len(result) == 3
    for _, rate in result:
        assert abs(rate - 2.00) < EPS


def test_231_pln_as_base_equals_one_divided_by_quote_pln_rate():
    """
    Manual calculation:
        USD/PLN = 4.00
        PLN/USD = 1 / 4.00 = 0.25  (exact)
    """
    c = CERCAS()
    c.base = "PLN"
    c.quote = "USD"
    d = datetime(2023, 1, 2)
    result = c.build_cross_rate_series([], [(d, 4.00)])
    assert len(result) == 1
    assert abs(result[0][1] - 0.25) < EPS


def test_231_pln_as_quote_cross_rate_equals_base_pln_rate_directly():
    """
    Manual calculation:
        EUR/PLN = 4.20  ->  no division needed, rate = 4.20  (exact)
    """
    c = CERCAS()
    c.base = "EUR"
    c.quote = "PLN"
    d = datetime(2023, 1, 2)
    result = c.build_cross_rate_series([(d, 4.20)], [])
    assert len(result) == 1
    assert abs(result[0][1] - 4.20) < EPS


# =============================================================================
# SRS 2.3.2 – Daily change calculation
# "The system shall calculate daily changes as the difference between
#  the current session closing exchange rate and the previous closing
#  exchange rate."
# =============================================================================

def test_232_daily_change_equals_current_rate_minus_previous_rate():
    """
    Manual calculation:
        rate[Jan 2] = 1.00,  rate[Jan 3] = 1.10
        change[Jan 3] = 1.10 - 1.00 = +0.10  (exact)
    """
    c = CERCAS()
    series = [
        (datetime(2023, 1, 2), 1.00),
        (datetime(2023, 1, 3), 1.10),
    ]
    result = c.compute_daily_changes(series)
    assert len(result) == 1
    assert abs(result[0] - 0.10) < EPS


def test_232_daily_change_is_negative_when_rate_falls():
    """
    Manual calculation:
        rate[Jan 2] = 1.10,  rate[Jan 3] = 1.00
        change[Jan 3] = 1.00 - 1.10 = -0.10  (exact)
    """
    c = CERCAS()
    series = [
        (datetime(2023, 1, 2), 1.10),
        (datetime(2023, 1, 3), 1.00),
    ]
    result = c.compute_daily_changes(series)
    assert abs(result[0] - (-0.10)) < EPS


def test_232_n_sessions_produce_n_minus_1_daily_changes():
    """
    Manual reasoning:
        5 sessions -> 4 daily changes
        (the first session has no previous session to compare against)
    """
    c = CERCAS()
    series = [(datetime(2023, 1, i), float(i)) for i in range(2, 7)]  # 5 elements
    result = c.compute_daily_changes(series)
    assert len(result) == 4


def test_232_three_consecutive_rates_produce_correct_two_changes():
    """
    Manual calculation:
        rate[Jan 2] = 2.00,  rate[Jan 3] = 2.20,  rate[Jan 4] = 2.10
        change[Jan 3] = 2.20 - 2.00 = +0.20
        change[Jan 4] = 2.10 - 2.20 = -0.10
    """
    c = CERCAS()
    series = [
        (datetime(2023, 1, 2), 2.00),
        (datetime(2023, 1, 3), 2.20),
        (datetime(2023, 1, 4), 2.10),
    ]
    result = c.compute_daily_changes(series)
    assert len(result) == 2
    assert abs(result[0] - (+0.20)) < EPS
    assert abs(result[1] - (-0.10)) < EPS


# =============================================================================
# SRS 2.3.4 – Histogram
# "The system shall group daily changes into dynamically calculated
#  value ranges based on the entered number of intervals."
# =============================================================================

def test_234_histogram_step_width_equals_range_divided_by_n():
    """
    Manual calculation:
        values = [-0.10, +0.20],  N = 3
        range  = 0.20 - (-0.10) = 0.30
        step   = 0.30 / 3       = 0.10  (exact)
    Verified via: end_of_bin_0 - start_of_bin_0.
    """
    c = CERCAS()
    c.number_of_intervals = 3
    result = c.build_histogram([-0.10, 0.20])
    step = result[0][1] - result[0][0]
    assert abs(step - 0.10) < EPS


def test_234_histogram_returns_exactly_n_bins():
    """
    Manual reasoning:  N = 4 intervals -> exactly 4 bins returned.
    """
    c = CERCAS()
    c.number_of_intervals = 4
    result = c.build_histogram([-0.10, -0.05, 0.05, 0.10, 0.20])
    assert len(result) == 4


def test_234_sum_of_all_bin_frequencies_equals_number_of_values():
    """
    Manual reasoning:
        6 daily change values, N = 3
        Each value goes to exactly one bin -> total frequencies = 6.
    """
    c = CERCAS()
    c.number_of_intervals = 3
    values = [-0.20, -0.10, 0.00, 0.10, 0.20, 0.30]
    result = c.build_histogram(values)
    assert sum(freq for _, _, freq in result) == len(values)


def test_234_maximum_value_is_placed_in_last_bin_not_overflowed():
    """
    Manual calculation:
        values = [0.0, 0.1, 0.2, 0.3],  N = 3
        min = 0.0,  max = 0.3,  step = 0.3 / 3 = 0.1

        Bin 0: [0.0, 0.1)  ->  0.0          -> freq = 1
        Bin 1: [0.1, 0.2)  ->  0.1          -> freq = 1
        Bin 2: [0.2, 0.3]  ->  0.2 and 0.3  -> freq = 2
          (max value 0.3: idx = int(0.3/0.1) = 3 -> clamped to last bin 2)
    """
    c = CERCAS()
    c.number_of_intervals = 3
    result = c.build_histogram([0.0, 0.1, 0.2, 0.3])
    assert result[2][2] == 2   # last bin must contain both 0.2 and 0.3


def test_234_bin_frequencies_match_manual_calculation():
    """
    Manual calculation:
        values = [-0.10, +0.20],  N = 2
        min = -0.10,  max = +0.20,  step = 0.30 / 2 = 0.15

        Bin 0: [-0.10,  0.05)  ->  -0.10  -> freq = 1
        Bin 1: [ 0.05,  0.20]  ->  +0.20  -> freq = 1
          (+0.20: idx = int(0.30/0.15) = int(2.0) = 2 -> clamped to bin 1)
    """
    c = CERCAS()
    c.number_of_intervals = 2
    result = c.build_histogram([-0.10, 0.20])
    assert result[0][2] == 1   # bin 0 frequency
    assert result[1][2] == 1   # bin 1 frequency


# =============================================================================
# SRS 2.4.1 / 2.4.2 / 2.4.3 – CSV export
# =============================================================================

def test_241_export_creates_a_file_on_disk():
    """SRS 2.4.1: the system shall allow exporting processed data into CSV files."""
    c = CERCAS()
    c.histogram = [(0.0, 1.0, 3)]
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        c.export(path)
        assert os.path.isfile(path)
    finally:
        os.unlink(path)


def test_242_export_rejects_path_without_csv_extension(capsys):
    """SRS 2.4.2: output file name shall use the '.csv' extension."""
    c = CERCAS()
    c.histogram = [(0.0, 1.0, 3)]
    c.export("result.txt")
    assert ".csv" in capsys.readouterr().out


def test_243_first_line_of_csv_is_the_required_header():
    """
    SRS 2.4.3: CSV header must be exactly:
        interval_start;interval_end;frequency
    """
    c = CERCAS()
    c.histogram = [(-0.10, 0.05, 1), (0.05, 0.20, 1)]
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        c.export(path)
        with open(path, encoding="utf-8") as f:
            header = f.readline().strip()
        assert header == "interval_start;interval_end;frequency"
    finally:
        os.unlink(path)


def test_243_csv_data_rows_are_separated_by_semicolons():
    """SRS 2.4.3: semicolon-separated format – each data row must have exactly 3 fields."""
    c = CERCAS()
    c.histogram = [(-0.10, 0.05, 1), (0.05, 0.20, 1)]
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        c.export(path)
        with open(path, encoding="utf-8") as f:
            rows = [line.strip() for line in f if line.strip()]
        for row in rows[1:]:   # skip header
            assert len(row.split(";")) == 3
    finally:
        os.unlink(path)


def test_243_csv_frequency_values_match_manually_computed_histogram():
    """
    Manual calculation:
        values = [-0.10, +0.20],  N = 2
        step = 0.30 / 2 = 0.15

        Bin 0: [-0.10, 0.05)  ->  -0.10  ->  freq = 1
        Bin 1: [ 0.05, 0.20]  ->  +0.20  ->  freq = 1

    Expected CSV (after header):
        2 data rows, each with frequency = 1.
    """
    c = CERCAS()
    c.histogram = [(-0.10, 0.05, 1), (0.05, 0.20, 1)]
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        c.export(path)
        with open(path, encoding="utf-8") as f:
            rows = [line.strip() for line in f if line.strip()]
        assert len(rows) == 3   # 1 header + 2 data rows
        assert int(rows[1].split(";")[2]) == 1
        assert int(rows[2].split(";")[2]) == 1
    finally:
        os.unlink(path)


# =============================================================================
# Full pipeline integration – SRS 2.3.1, 2.3.2, 2.3.4
# =============================================================================

def test_full_pipeline_eur_usd_histogram_matches_manual_calculation():
    """
    End-to-end test with mocked NBP API. All expected values computed by hand.

    Input (USD/PLN held constant at 1.00 so cross-rate = EUR/PLN directly):
        EUR/PLN:  Jan 1 -> 1.00
                  Jan 2 -> 1.10
                  Jan 3 -> 1.20
                  Feb 1 -> 1.30
                  Feb 2 -> 1.10
        USD/PLN:  all five dates -> 1.00

    Step 1 - Cross-rate (SRS 2.3.1):
        EUR/USD = EUR/PLN / USD/PLN = EUR/PLN  (since USD/PLN = 1.00)
        Series: 1.00 -> 1.10 -> 1.20 -> 1.30 -> 1.10

    Step 2 - Daily changes (SRS 2.3.2):
        Jan 2:  1.10 - 1.00 = +0.10
        Jan 3:  1.20 - 1.10 = +0.10
        Feb 1:  1.30 - 1.20 = +0.10
        Feb 2:  1.10 - 1.30 = -0.20
        Total: 4 daily changes

    Step 3 - Histogram N=2 (SRS 2.3.4):
        min = -0.20,  max = +0.10
        step = (0.10 - (-0.20)) / 2 = 0.30 / 2 = 0.15

        Bin 0: [-0.20, -0.05)  ->  -0.20              -> freq = 1
        Bin 1: [-0.05, +0.10]  ->  +0.10, +0.10, +0.10 -> freq = 3
    """
    eur_rates = [
        (datetime(2023, 1, 1), 1.00),
        (datetime(2023, 1, 2), 1.10),
        (datetime(2023, 1, 3), 1.20),
        (datetime(2023, 2, 1), 1.30),
        (datetime(2023, 2, 2), 1.10),
    ]
    usd_rates = [(d, 1.00) for d, _ in eur_rates]

    def mock_fetch(currency):
        return eur_rates if currency == "EUR" else usd_rates

    c = CERCAS()
    c.base                = "EUR"
    c.quote               = "USD"
    c.start_date          = datetime(2023, 1, 1)
    c.aggregation_type    = AggregationType.MONTHLY
    c.number_of_intervals = 2

    with patch.object(c, 'fetch_rates', side_effect=mock_fetch):
        c.run_analysis()

    assert c.histogram is not None
    assert len(c.histogram) == 2

    # Total frequencies must equal 4 (one per daily change)
    assert sum(freq for _, _, freq in c.histogram) == 4

    # Bin 0: freq=1 (-0.20), Bin 1: freq=3 (three +0.10 changes)
    assert c.histogram[0][2] == 1
    assert c.histogram[1][2] == 3


# =============================================================================
# Issue #28 – Export Analysis frequency some data is lost
# "When exported histogram has less data in frequency when it should have."
# The sum of all bin frequencies in the exported CSV must equal the number
# of daily changes. No data should be lost during export.
# =============================================================================

def test_issue28_exported_frequency_sum_equals_number_of_daily_changes():
    """
    Regression test for Issue #28.

    Manual calculation (same data as full pipeline test):
        4 daily changes -> histogram total frequency must be 4.
        After export to CSV, sum of all frequency fields must also equal 4.
    """
    eur_rates = [
        (datetime(2023, 1, 1), 1.00),
        (datetime(2023, 1, 2), 1.10),
        (datetime(2023, 1, 3), 1.20),
        (datetime(2023, 2, 1), 1.30),
        (datetime(2023, 2, 2), 1.10),
    ]
    usd_rates = [(d, 1.00) for d, _ in eur_rates]

    def mock_fetch(currency):
        return eur_rates if currency == "EUR" else usd_rates

    c = CERCAS()
    c.base                = "EUR"
    c.quote               = "USD"
    c.start_date          = datetime(2023, 1, 1)
    c.aggregation_type    = AggregationType.MONTHLY
    c.number_of_intervals = 2

    with patch.object(c, 'fetch_rates', side_effect=mock_fetch):
        c.run_analysis()

    assert c.histogram is not None

    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        c.export(path)
        with open(path, encoding="utf-8") as f:
            rows = [line.strip() for line in f if line.strip()]
        data_rows = rows[1:]  # skip header
        assert len(data_rows) == 2, "Exported CSV must contain all bins"
        total_exported_freq = sum(int(row.split(";")[2]) for row in data_rows)
        assert total_exported_freq == 4, (
            f"Issue #28: exported frequency sum is {total_exported_freq}, expected 4 — data was lost"
        )
    finally:
        os.unlink(path)