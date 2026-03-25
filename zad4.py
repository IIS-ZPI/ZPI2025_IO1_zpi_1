from abc import ABC, abstractmethod

class IArithmeticsDiff():
    @abstractmethod
    def Difference(self, A : float, B : float) -> float:
        pass

class ArithmeticsDiff(IArithmeticsDiff):
    def Difference(self, A : float, B : float) -> float:
        return A - B