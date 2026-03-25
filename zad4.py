from abc import ABC, abstractmethod


class IArithmeticsMult(ABC):
    @abstractmethod
    def multiplication(self, a, b):
        pass

class IArithmeticsDiv(ABC):
    @abstractmethod
    def division(self, a, b):
        pass

class ArithmeticsMult(IArithmeticsMult):
    def multiplication(self, a, b):
        return a * b

class ArithmeticDiv(IArithmeticsDiv):
    def division(self, a, b):
        if b == 0:
            print("ERROR, cannot divide by 0")
        return a / b


