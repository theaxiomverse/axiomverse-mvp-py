from .holographic_interface import HolographicInterface

class HolographicScreen(HolographicInterface):
    def __init__(self, area, gravitational_constant=1.0):
        self.area = area
        self.G = gravitational_constant

    def holographic_entropy(self) -> float:
        return self.area / (4 * self.G)
