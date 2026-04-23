from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from requests import get
from src.app.core.currency_validator import validate_currency
from src.app.core.aggregation_type import AggregationType


class CERCAS:
    def __init__(self):
        self.histogram = None
        self.base: str | None = None
        self.base_table: str | None = None
        self.quote: str | None = None
        self.quote_table: str | None = None
        self.start_date: datetime | None = None
        self.end_date: datetime | None = None
        self.aggregation_type: AggregationType | None = None
        self.number_of_intervals: int | None = None

    def set_pair(self, base: str, quote: str) -> None:
        try:
            base = base.upper()
            quote = quote.upper()

            validate_currency(base)
            validate_currency(quote)

            self.base = base.upper()
            self.quote = quote.upper()

            print("Pair set successfully")
        except Exception as e:
            print(f"An error occurred: {e}")
            return

    def set_period(self, start_date: datetime, end_date: datetime) -> None:
        try:
            if start_date + relativedelta(months=3) < end_date:
                raise ValueError(
                    f"period can't be longer then 3 months"
                )

            if start_date < datetime(2002, 1, 2):
                raise ValueError(
                    f"start_date must be after 2002-01-02"
                )

            if end_date < start_date:
                raise ValueError(
                    f"start_date ({start_date}) must be greater than end_date ({end_date})"
                )

            if start_date > datetime.now():
                raise ValueError(
                    f"start_date can't be in future."
                )

            self.start_date = start_date
            self.end_date = end_date

            print("Period set successfully")
        except Exception as e:
            print(f"An error occurred: {e}")

    def set_type(self, type: AggregationType) -> None:
        self.aggregation_type = type

        print("Aggregation type set successfully")

    def set_interval(self, number: int) -> None:
        try:
            if number >= 0:
                self.number_of_intervals = number
            else:
                raise ValueError("Interval must be positive")

            print("Interval set successfully")
        except Exception as e:
            print(f"An error occurred: {e}")

    def run_analysis(self) -> None:
        try:
            if self.base is None or self.quote is None:
                raise ValueError("Currency pair not set.")

            if self.start_date is None or self.end_date is None:
                raise ValueError("Period not set.")

            if self.aggregation_type is None:
                raise ValueError("Aggregation type not set.")

            if self.number_of_intervals is None:
                raise ValueError("Intervals not set.")

            print("Analysis started")

            base_rates = self.__fetch_rates(self.base)
            quote_rates = self.__fetch_rates(self.quote)

            series = self.__build_cross_rate_series(base_rates, quote_rates)

            if len(series) < 2:
                raise ValueError("Not enough data points returned from NBP API.")

            daily_changes = self.__daily_changes(series)
            aggregated_values = self.__aggregate_changes(daily_changes)

            self.histogram = self.__build_histogram(aggregated_values)

            print("Analysis completed successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def export(self, file_path: str) -> None:
        try:
            if self.histogram is None:
                raise ValueError("No analysis results to export. Run analysis first.")

            if not file_path.endswith(".csv"):
                raise ValueError("Export file must have .csv extension.")

            with open(file_path, "w", encoding="utf-8") as f:
                f.write("interval_start;interval_end;frequency\n")
                for start, end, freq in self.histogram:
                    f.write(f"{start};{end};{freq}\n")

            print(f"Exported successfully to {file_path}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def show_config(self) -> None:
        if self.base is None:
            print(f"Base currency isn't set.")
            print(f"Quote currency isn't set.")
        else:
            print(f"Base currency is: {self.base}")
            print(f"Quote currency is: {self.quote}")

        if self.start_date is None:
            print(f"Start date isn't set.")
            print(f"End date isn't set.")
        else:
            print(f"Start date is: {self.start_date.date()}")
            print(f"End date is: {self.end_date.date()}")

        if self.aggregation_type is None:
            print(f"Aggregation level for the analysis isn't set.")
        elif self.aggregation_type == AggregationType.MONTHLY:
            print(f"Aggregation level for the analysis is set to monthly.")
        else:
            print(f"Aggregation level for the analysis is set to quarterly.")

        if self.number_of_intervals is None:
            print(f"Number of intervals isn't set.")
        else:
            print(f"Number of intervals is: {self.number_of_intervals}")

    def __fetch_rates(self, currency: str) -> list[tuple[datetime, float]]:
        if currency == "PLN":
            return []

        currency_api = currency.lower()

        all_rates: list[tuple[datetime, float]] = []

        current_start = self.start_date
        while current_start <= self.end_date:
            current_end = min(current_start + timedelta(days=360), self.end_date)

            start_str = current_start.strftime("%Y-%m-%d")
            end_str = current_end.strftime("%Y-%m-%d")

            success = False

            for table in ["A", "B"]:
                url = f"https://api.nbp.pl/api/exchangerates/rates/{table}/{currency_api}/{start_str}/{end_str}/?format=json"
                r = get(url)

                if r.status_code == 200:
                    data = r.json()
                    all_rates.extend(
                        (datetime.strptime(x["effectiveDate"], "%Y-%m-%d"), x["mid"])
                        for x in data["rates"]
                    )
                    success = True
                    break

            if not success:
                raise ValueError(f"Currency {currency} not found in NBP Table A or B.")

            current_start = current_end + timedelta(days=1)

        return all_rates
    def __build_cross_rate_series(
            self,
            base_rates: list[tuple[datetime, float]],
            quote_rates: list[tuple[datetime, float]],
    ) -> list[tuple[datetime, float]]:
        """
        Returns aligned series of (date, base/quote).
        Uses intersection of available dates.
        """

        if self.base == "PLN":
            quote_map = {d: v for d, v in quote_rates}
            return [(d, 1.0 / quote_map[d]) for d in sorted(quote_map.keys())]

        if self.quote == "PLN":
            base_map = {d: v for d, v in base_rates}
            return [(d, base_map[d]) for d in sorted(base_map.keys())]

        base_map = {d: v for d, v in base_rates}
        quote_map = {d: v for d, v in quote_rates}

        common_dates = sorted(set(base_map.keys()) & set(quote_map.keys()))
        return [(d, base_map[d] / quote_map[d]) for d in common_dates]

    def __daily_changes(self, series: list[tuple[datetime, float]]) -> list[tuple[datetime, float]]:
        """
        Returns list of (date, change) where change = rate(today) - rate(yesterday)
        """
        changes = []
        for i in range(1, len(series)):
            date_today, rate_today = series[i]
            _, rate_yesterday = series[i - 1]
            changes.append((date_today, rate_today - rate_yesterday))
        return changes

    def __get_period_key(self, date: datetime) -> tuple[int, int]:
        """
        Returns (year, month) for monthly
        Returns (year, quarter) for quarterly
        """
        if self.aggregation_type == AggregationType.MONTHLY:
            return (date.year, date.month)

        quarter = (date.month - 1) // 3 + 1
        return (date.year, quarter)

    def __aggregate_changes(self, changes: list[tuple[datetime, float]]) -> list[float]:
        """
        Aggregate daily changes into monthly or quarterly sums.
        Returns list of aggregated values.
        """
        aggregated = {}
        for date, change in changes:
            key = self.__get_period_key(date)
            aggregated[key] = aggregated.get(key, 0.0) + change

        return [aggregated[k] for k in sorted(aggregated.keys())]

    def __build_histogram(self, values: list[float]) -> list[tuple[float, float, int]]:
        """
        Build histogram based on number_of_intervals.
        Returns list of (interval_start, interval_end, frequency)
        """
        if not values:
            raise ValueError("No values to build histogram.")

        min_v = min(values)
        max_v = max(values)

        if min_v == max_v:
            # all values same -> single bin
            return [(min_v, max_v, len(values))]

        step = (max_v - min_v) / self.number_of_intervals

        bins = []
        for i in range(self.number_of_intervals):
            start = min_v + i * step
            end = min_v + (i + 1) * step
            bins.append([start, end, 0])

        for v in values:
            idx = int((v - min_v) / step)
            if idx == self.number_of_intervals:
                idx -= 1
            bins[idx][2] += 1

        return [(b[0], b[1], b[2]) for b in bins]