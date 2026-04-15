import cmd
from src.app.core.cercas import CERCAS
from datetime import datetime

class CERCASShell(cmd.Cmd):
    intro = 'Welcome to C.E.R.C.A.S. CLI Shell.'
    prompt = ""

    def __init__(self):
        super().__init__()
        self.app = CERCAS()

    # exit
    def do_exit(self, arg):
        exit(0)

    # set_pair <base>/<quote>
    def do_set_pair(self, arg):
        try:
            base, quote = arg.strip().split('/')
            self.app.set_pair(base, quote)
        except ValueError:
            print("Usage: set_pair <base>/<quote> (example: EUR/USD)")

    # set_period <start_date> <end_date>
    def do_set_period(self, arg):
        try:
            start_date, end_date = arg.strip().split(' ')
            self.app.set_period(start_date, end_date)
        except ValueError:
            print("Usage: set_period <start_date> <end_date>")

    # set_type <type>
    def do_set_type(self, arg):
        try:
            type = arg
            self.app.set_type(type)
        except ValueError:
            print("Usage: set_type <type>")

    # set_interval <number>
    def do_set_interval(self, arg):
        try:
            number = arg
            self.app.set_interval(number)
        except ValueError:
            print("Usage: set_interval <number>")

    # export <file_path>
    def do_export(self, arg):
        try:
            file_path = arg
            self.app.export(file_path)
        except ValueError:
            print("Usage: export <file_path>")

    # run_analysis
    def do_run_analysis(self):
        try:
            self.app.run_analysis()
        except ValueError:
            print("Usage: run_analysis")

    # show_config
    def do_show_config(self, arg):
        self.app.show_config()
