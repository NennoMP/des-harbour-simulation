import random
import simpy

from logger import dock_logger


# -------------------------
# SIMPY CONFIGURATION
# -------------------------
BARGE_REFUEL_TIME = 1
BARGE_REFUEL_STD = 0.25


class FuelBarge:
    """Class representing a fuel barge used to do the bunkering of another sheap.
    """

    # Environment
    env: simpy.Environment

    # Attributes
    id: int
    fuel_tank: simpy.Container # simulates fuel tank
    fuel_capacity: int = 100_000 # (in liters)
    tank_threshold_percentage = 20 # (as percentage %)
    tank_threshold: int

    def __init__(self, env: simpy.Environment, id: int):
        """Initializes the class.

        :param <env>: simulation (simpy) environment
        :param <id>: id of the current fuel barge
        """

        self.env = env

        self.id = id
        self.fuel_tank = simpy.Container(
            env, 
            init=self.fuel_capacity, 
            capacity=self.fuel_capacity)
        self.tank_threshold = int(
            (self.fuel_capacity*self.tank_threshold_percentage)/100)

    def check_fuel_tank(self):
        """Checks if <fuel_tank.level> is under a threshold, refuel if true."""

        if self.fuel_tank.level < self.tank_threshold:
            dock_logger.info(f'[{self.env.now:.3f}]: FuelBarge {self.id} refuels at tank level {self.fuel_tank.level:.0f}.')

            # Wait refueling to be completed
            yield self.env.process(self.barge_refuel(self.env))
            
    def barge_refuel(self):
        """Simulates barge refueling with a gaussian (normal) distribution."""
        
        # Gaussian (normal) distribution
        yield self.env.timeout(
            abs(random.gauss(BARGE_REFUEL_TIME, BARGE_REFUEL_STD)))

        # Refuel missing quantity
        missing = self.fuel_tank.capacity - self.fuel_tank.level
        yield self.fuel_tank.put(missing)

        dock_logger.info(f'[{self.env.now:.3f}]: FuelBarge {self.id} refueled!')