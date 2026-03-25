from abc import ABC, abstractmethod
#komentarz wiktora 1
class IArithmeticsAdd(ABC):
    @abstractmethod
    def Addition(self, a,b):
        pass

class ArithmeticsAdd(IArithmeticsAdd):
    def Addition(self, a, b):
        return a + b
    
class IArithmeticsDiff(ABC):
    @abstractmethod
    def Difference(self, A : float, B : float) -> float:
        pass

class ArithmeticsDiff(IArithmeticsDiff):
    def Difference(self, A : float, B : float) -> float:
        return A - B
#komentarz testera 2
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
#komentarz testera 3
class ArithmeticDiv(IArithmeticsDiv):
    def division(self, a, b):
        if b == 0:
            print("ERROR, cannot divide by 0")
        return a / b
