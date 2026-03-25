from abc import ABC, abstractmethod

class IArithmeticsAdd(ABC):
    @abstractmethod
    def Addition(self, a,b):
        pass

class ArithmeticsAdd(IArithmeticsAdd):
    def Addition(self, a, b):
        return a + b