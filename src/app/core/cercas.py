from datetime import datetime, timedelta
from requests import get
from app.core.currency_validator import validate_currency
from app.core.aggregation_type import AggregationType


class CERCAS:
    def __init__(self):
        self.histogram = None
        self.base: str | None = None
        self.quote: str | None = None
        self.start_date: datetime | None = None
        self.aggregation_type: AggregationType | None = None
        self.number_of_intervals: int | None = None

    def set_pair(self, base: str, quote: str) -> None:
        try:
            base = base.upper()
            quote = quote.upper()

            validate_currency(base)
            validate_currency(quote)

            self.base = base
            self.quote = quote

            print("Pair set successfully")
        except Exception as e:
            print(f"An error occurred: {e}")

    def set_start(self, start_date: datetime) -> None:
        try:
            if start_date < datetime(2002, 1, 2):
                raise ValueError("start_date must be after 2002-01-02")

            if start_date > datetime.now():
                raise ValueError("start_date can't be in the future")

            self.start_date = start_date
            print("Start date set successfully")
        except Exception as e:
            print(f"An error occurred: {e}")

    def set_type(self, type: AggregationType) -> None:
        self.aggregation_type = type
        print("Aggregation type set successfully")

    def switch_type(self) -> None:
        if self.aggregation_type is None:
            raise ValueError("You must set aggregation before you can switch it.")
        if self.aggregation_type is AggregationType.QUARTERLY:
            self.aggregation_type = AggregationType.MONTHLY
        else:
            self.aggregation_type = AggregationType.QUARTERLY
        print(f"Aggregation type switched to {self.aggregation_type.value}")

    def set_interval(self, number: int) -> None:
        try:
            if number > 0:
                self.number_of_intervals = number
            else:
                raise ValueError("Interval must be positive")
            print("Interval set successfully")
        except Exception as e:
            print(f"An error occurred: {e}")

    def __get_end_date(self) -> datetime:
        if self.aggregation_type == AggregationType.MONTHLY:
            return self.start_date + timedelta(days=30)
        else:
            return self.start_date + timedelta(days=90)

    def run_analysis(self) -> None:
        try:
            if self.base is None or self.quote is None:
                raise ValueError("Currency pair not set.")

            if self.start_date is None:
                raise ValueError("Start date not set.")

            if self.aggregation_type is None:
                raise ValueError("Aggregation type not set.")

            if self.number_of_intervals is None:
                raise ValueError("Intervals not set.")

            print("Analysis started")

            base_rates = self.fetch_rates(self.base)
            quote_rates = self.fetch_rates(self.quote)

            series = self.build_cross_rate_series(base_rates, quote_rates)

            if len(series) < 2:
                raise ValueError("Not enough data points returned from NBP API.")

            daily_changes = self.compute_daily_changes(series)

            self.histogram = self.build_histogram(daily_changes)

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
            print("Base currency isn't set.")
            print("Quote currency isn't set.")
        else:
            print(f"Base currency is: {self.base}")
            print(f"Quote currency is: {self.quote}")

        if self.start_date is None:
            print("Start date isn't set.")
        elif self.aggregation_type is not None:
            end_date = self.__get_end_date()
            print(f"Period: {self.start_date.date()} → {end_date.date()}")
        else:
            print(f"Start date is: {self.start_date.date()}")
            print("End date: not available yet (set aggregation type first)")

        if self.aggregation_type is None:
            print("Aggregation level for the analysis isn't set.")
        elif self.aggregation_type == AggregationType.MONTHLY:
            print("Aggregation level for the analysis is set to monthly.")
        else:
            print("Aggregation level for the analysis is set to quarterly.")

        if self.number_of_intervals is None:
            print("Number of intervals isn't set.")
        else:
            print(f"Number of intervals is: {self.number_of_intervals}")

    def fetch_rates(self, currency: str) -> list[tuple[datetime, float]]:
        return self.__fetch_rates(currency)

    def __fetch_rates(self, currency: str) -> list[tuple[datetime, float]]:
        if currency == "PLN":
            return []

        end_date = self.__get_end_date()
        start_str = self.start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        currency_api = currency.lower()

        url = f"https://api.nbp.pl/api/exchangerates/rates/A/{currency_api}/{start_str}/{end_str}/?format=json"

        r = get(url)

        if r.status_code == 200:
            data = r.json()
            return [
                (datetime.strptime(x["effectiveDate"], "%Y-%m-%d"), x["mid"])
                for x in data["rates"]
            ]

        raise ValueError(f"Currency {currency} not found in NBP Table A or B.")

    def build_cross_rate_series(
        self,
        base_rates: list[tuple[datetime, float]],
        quote_rates: list[tuple[datetime, float]],
    ) -> list[tuple[datetime, float]]:
        """
        Returns aligned series of (date, base/quote).
        Uses intersection of available dates.

        NBP always quotes against PLN, so:
          - base_rates  = base/PLN
          - quote_rates = quote/PLN
          - cross rate  = base/PLN ÷ quote/PLN = base/quote
        """
        if self.base == "PLN":
            # PLN/quote = 1 / (quote/PLN)
            quote_map = {d: v for d, v in quote_rates}
            return [(d, 1.0 / quote_map[d]) for d in sorted(quote_map.keys())]

        if self.quote == "PLN":
            # base/PLN directly from NBP
            base_map = {d: v for d, v in base_rates}
            return [(d, base_map[d]) for d in sorted(base_map.keys())]

        # general cross rate: base/quote via PLN
        base_map = {d: v for d, v in base_rates}
        quote_map = {d: v for d, v in quote_rates}

        common_dates = sorted(set(base_map.keys()) & set(quote_map.keys()))
        return [(d, base_map[d] / quote_map[d]) for d in common_dates]

    def compute_daily_changes(
        self, series: list[tuple[datetime, float]]
    ) -> list[float]:
        """
        Returns list of daily changes: rate(today) - rate(yesterday).
        Each value represents one trading session's movement.
        """
        return [
            series[i][1] - series[i - 1][1]
            for i in range(1, len(series))
        ]

    def build_histogram(self, values: list[float]) -> list[tuple[float, float, int]]:
        """
        Builds a frequency histogram over daily changes.
        Divides [min, max] into number_of_intervals equal bins.
        Returns list of (interval_start, interval_end, frequency).
        Frequencies sum to len(values).
        """
        if not values:
            raise ValueError("No values to build histogram.")

        min_v = min(values)
        max_v = max(values)

        if min_v == max_v:
            raise ValueError(
                "All daily changes are identical — histogram is trivial."
            )

        step = (max_v - min_v) / self.number_of_intervals

        bins = [[min_v + i * step, min_v + (i + 1) * step, 0]
                for i in range(self.number_of_intervals)]

        for v in values:
            idx = int((v - min_v) / step)
            idx = min(idx, self.number_of_intervals - 1)
            bins[idx][2] += 1

        return [(b[0], b[1], b[2]) for b in bins]