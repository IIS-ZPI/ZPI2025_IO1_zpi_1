import cmd

from src.app.core.aggregation_type import AggregationType
from src.app.core.cercas import CERCAS
from datetime import datetime

class CERCASShell(cmd.Cmd):
    intro = 'Welcome to C.E.R.C.A.S. CLI Shell.'
    prompt = ""

    def __init__(self):
        super().__init__()
        self.app = CERCAS()

    # exit
    def do_exit(self, arg) -> None:
        """
        exit
        Description: Exit the shell
        Parameters: None

        """
        exit(0)

    # set_pair <base>/<quote>
    def do_set_pair(self, arg) -> None:
        """
        set_pair <base>/<quote>
        Description: Set the currency pairs used for analysis.
        Parameters:
        ● base - base currency code in ISO 4217 format (e.g. EUR)
        ● quote - quoted currency code in ISO 4217 format (e.g. USD)

        """
        try:
            base, quote = arg.strip().split('/')
            self.app.set_pair(base, quote)
        except ValueError:
            print("Usage: set_pair <base>/<quote> (example: EUR/USD)")

    # set_period <start_date> <end_date>
    def do_set_period(self, arg) -> None:
        """
        set_period <start_date> <end_date>
        Description: Define the time range for the analysis.
        Parameters:
        ● start_date - start date in yyyy-mm-dd format
        ● end_date - end date in yyyy-mm-dd format

        """
        try:
            start_date, end_date = arg.strip().split(' ')
            y, m, d = start_date.split('-')
            start_date = datetime(int(y), int(m), int(d))
            y, m, d = end_date.split('-')
            end_date = datetime(int(y), int(m), int(d))
            self.app.set_period(start_date, end_date)
        except ValueError:
            print("Usage: set_period <start_date> <end_date>")

    # set_aggregation <type>
    def do_set_aggregation(self, arg) -> None:
        """
        set_aggregation <type>
        Description: Set the aggregation level for the analysis.
        Parameters:
        ● type - aggregation type [MONTHLY / QUARTERLY]

        """

        if arg.upper() == "MONTHLY":
            self.app.set_type(AggregationType.MONTHLY)
        elif arg.upper() == "QUARTERLY":
            self.app.set_type(AggregationType.QUARTERLY)
        else:
            raise ValueError("Invalid aggregation type")
            #print("Usage: set_type <type>")

    # set_interval <number>
    def do_set_interval(self, arg) -> None:
        """
        Description: Define the number of intervals used to process data.
        Parameters:
        ● number - positive integer specifying the number of intervals

        """
        try:
            number : int = int(arg)
            self.app.set_interval(number)
        except ValueError:
            print("Usage: set_interval <number>")

    # export <file_path>
    def do_export(self, arg) -> None:
        """
        export <file_path>
        Description: Export the analysis results to a CSV file.
        Parameters:
        ● file_path - path to the output CSV file

        """
        try:
            file_path = arg
            self.app.export(file_path)
        except ValueError:
            print("Usage: export <file_path>")

    # run_analysis
    def do_run_analysis(self, arg) -> None:
        """
        run_analysis
        Description: Execute the analysis based on the currently defined parameters.
        Parameters: None

        """
        try:
            self.app.run_analysis()
        except ValueError:
            print("Usage: run_analysis")

    # show_config
    def do_show_config(self, arg) -> None:
        """
        show_config
        Description: Display the current analysis configuration.
        Parameters: None

        """
        self.app.show_config()
