from datetime import datetime
from requests import get

from src.app.core.currency_validator import validate_currency
from src.app.core.aggregation_type import AggregationType


class CERCAS:
    def __init__(self):
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
            validate_currency(base)
            validate_currency(quote)
        except Exception as e:
            print(f"An error occurred: {e}")
            return

        self.base = base.upper()
        self.quote = quote.upper()

        print("Pair set successfully")

    def set_period(self, start_date: datetime, end_date: datetime) -> None:
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

    def set_type(self, type: AggregationType) -> None:
        self.aggregation_type = type

        print("Aggregation type set successfully")

    def set_interval(self, number: int) -> None:
        if number >= 0:
            self.number_of_intervals = number
        else:
            raise ValueError("Interval must be positive")

        print("Interval set successfully")

    def run_analysis(self) -> None:
        pass

    def export(self, file_path: str) -> None:
        pass

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
