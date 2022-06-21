import random

# -------------------------
# SIMPY CONFIGURATION
# -------------------------
FUEL_CAPACITY_MEAN = 15
FUEL_CAPACITY_STD = 5 


class Ship(object):
    """Class representing a default ship object."""

    # Attributes
    id: int
    fuel_capacity: int # maximum fuel capacity
    fuel_level: int # current fuel level
    priority: int = 0 # ship priority
    
    def __init__(self, id: int):
        """Initializes the class.
        
        :param <id>: ship id
        """

        self.id = id

        # Generate random fuel capacity and level
        self.fuel_capacity = random.randint(5, 15) * 10_000
        self.fuel_level = int(
            random.uniform(self.fuel_capacity*0.4, self.fuel_capacity*0.8))

class SpecialShip(Ship):
    """Class representing a (special) higher priority ship object."""
    
    def __init__(self, id: int):
        """Initializes the class.
        
        :param <id>: special ship id
        """
        super().__init__(id)
        self.priority = -1
