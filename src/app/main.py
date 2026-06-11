# Methods add and multiply are added to show work of automatic unit tests,
# should be deleted later
# run method is not necessary to work, main is enough
from cli.shell import CERCASShell


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


def old_run():
    print("App running")
    print(add(2, 3))
    print(multiply(2, 3))

def run():
    CERCASShell().cmdloop()
    #query("A", "USD", "2020-01-02", "2020-01-02")

if __name__ == "__main__":
    run()