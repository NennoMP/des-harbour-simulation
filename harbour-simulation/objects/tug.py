import random
import simpy

from logger import arrival_logger

# -------------------------
# SIMPY CONFIGURATION
# -------------------------
TUG_MAINTENANCE_FREQUENCY = 24 # (daily)
TUG_MAINTENANCE_FREQUENCY_MEAN = 4

TUG_MAINTENANCE_TIME_MEAN = 5
TUG_MAINTENANCE_TIME_STD = 2
TUG_MAINTENANCE_LAMBDA = 1 / TUG_MAINTENANCE_TIME_MEAN

DOCKING_TIME_MEAN = 1
DOCKING_TIME_STD = 0.125


class Tug:
    """Class  representing a tug object."""

    # Environment
    env: simpy.Environment

    # Attributes
    id: int
    working: bool
    scheduled_maintenance: bool

    def __init__(self, env: simpy.Environment, id: int, tugs, monitor):
        """Initializes the class.
        
        :param <env>: simulation (simpy) environment
        :param <id>: tug id
        :param <tugs>: PriorityStore class instance
        :param <monitor>: SystemMonitor instance
        """

        self.env = env
        self.id = id
        self.working = False
        self.scheduled_maintenance = False

        # Set reference so SystemMonitor
        self.monitor = monitor

        self.tugs = tugs

        env.process(self.perform_maintance())

    def set_working(self, bool: bool):
        self.working = bool

    def set_maintenance(self, bool: bool):
        self.scheduled_maintenance = bool
    
    def transport(self):
        """Simulates docking/un-docking of a ship inside the harbour."""

        # Set current process
        self.action = self.env.active_process

        self.set_working(True)
        yield self.env.timeout(
            abs(random.gauss(DOCKING_TIME_MEAN, DOCKING_TIME_STD)))
        self.set_working(False)

    def perform_maintance(self):
        """Simulates periodic maintenance of a tug, if it is working wait for it to finish."""

        # Periodically perform maintenance
        while True:
            # Simulate wait for next maintenance
            yield self.env.timeout(abs(random.gauss(
                TUG_MAINTENANCE_FREQUENCY, 
                TUG_MAINTENANCE_FREQUENCY_MEAN)))

            # If tug working -> wait end of process
            if self.working:
                arrival_logger.info(f'[{self.env.now:.3f}]: Tug {self.id} scheduled for maintenance!')
                yield self.action

            # Remove tug from availables ones
            tug = yield self.tugs.get(
                priority=-3, 
                filter=lambda tug: tug.id == self.id)
            self.set_working(False)
            self.set_maintenance(True)

            self.monitor.start_maintenance()
            arrival_logger.info(f'[{self.env.now:.3f}]: Tug {tug.id} in maintenance!')

            # Simulate maintenance duration
            yield self.env.timeout(
                random.expovariate(
                    TUG_MAINTENANCE_LAMBDA
                )
            )

            # Make tug available again
            yield self.tugs.put(tug)
            
            self.monitor.maintenance_completed()
            self.set_maintenance(False)
            arrival_logger.info(f'[{self.env.now:.3f}]: Tug {self.id} finished maintenance!')
