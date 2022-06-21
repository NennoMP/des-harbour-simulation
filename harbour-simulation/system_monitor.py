import matplotlib.pyplot as plt
import simpy
from statistics import mean

from logger import queues_logger

# Files
PLOTS_PATH = 'harbour-simulation/data/plots/'


class SystemMonitor:
    """Class for monitoring environment state and resource usage."""

    # Environment
    env: simpy.Environment

    # Simulation globals
    sim_docks: int
    sim_tugs: int
    sim_barges: int

    # Arrivals states
    n_ships_system = 0
    n_ships_waiting = 0
    n_special_ships_waiting = 0
    n_tugs_in_use = 0
    n_docks_in_use = 0
    n_ships_supplied = 0
    n_tugs_in_maintenance = 0

    ships_system = []
    ships_waiting = []
    special_ships_waiting = []
    tugs_in_use = []
    docks_in_use = []
    ships_supplied = []
    tugs_in_maintenance = []

    # Docks states
    n_ships_docked = 0
    n_ships_waiting_bunkering = 0
    n_ships_bunkering = 0
    n_barges_in_use = 0

    ships_docked = []
    ships_waiting_bunkering = []
    ships_bunkering = []
    barges_in_use = []

    # Queues wait times
    entrance_queue = []
    bunkering_queue = []
    exit_queue = []


    def init(self, env: simpy.Environment, sim_docks: int, sim_tugs: int, sim_barges: int):
        """Initializes the class.

        :param <env>: simulation (simpy) environment
        :param <sim_docks>: number of docks of current simulation
        :param <sim_tugs>: number of tugs of current simulation
        :param <sim_barges>: number of barges of current simulation
        """

        self.env = env

        self.sim_docks = sim_docks
        self.sim_tugs = sim_tugs
        self.sim_barges = sim_barges

        self.ships_system.append((self.env.now, self.n_ships_system))
        self.ships_waiting.append((self.env.now, self.n_ships_waiting))
        self.tugs_in_use.append((self.env.now, self.n_tugs_in_use))
        self.docks_in_use.append((self.env.now, self.n_docks_in_use))
        self.ships_supplied.append((self.env.now, self.n_ships_supplied))
        self.tugs_in_maintenance.append((self.env.now, self.n_tugs_in_maintenance))

        self.ships_docked.append((self.env.now, self.n_ships_docked))
        self.ships_waiting_bunkering.append((self.env.now, self.n_ships_waiting_bunkering))
        self.ships_bunkering.append((self.env.now, self.n_tugs_in_use))
        self.docks_in_use.append((self.env.now, self.n_ships_bunkering))
        self.barges_in_use.append((self.env.now, self.n_barges_in_use))

    def add_to_entrance_queue(self, wait_time: float):
        """Add entry to entrance waiting times list (obtained a dock && a tug).

        :param <wait_time>: the time waited by a ship before starting docking
        """
        self.entrance_queue.append(wait_time)

    def add_to_bunkering_queue(self, wait_time: float):
        """Add entry to bunkering waiting times list (obtained a barge).

        :param <wait_time>: the time waited by a ship before starting bunkering
        """
        self.bunkering_queue.append(wait_time)

    def add_to_exit_queue(self, wait_time: float):
        """Add entry to exit waiting times list (obtained a tug).

        :param <wait_time>: the time waited by a ship before starting to exit
        """
        self.exit_queue.append(wait_time)

    def new_ship(self, prio: int):
        """Store the state changes due to the arrival of a new ship.
        
        :param <prio>: arrived ship priority
        """

        self.n_ships_system += 1
        self.ships_system.append((self.env.now, self.n_ships_system))

        if prio == 0:
            self.n_ships_waiting += 1
            self.ships_waiting.append((self.env.now, self.n_ships_waiting))
        else:
            self.n_special_ships_waiting += 1
            self.special_ships_waiting.append((self.env.now, self.n_special_ships_waiting))

    def start_docking(self, prio: int):
        """Store the state changes due to the beginning of a ship docking.
        
        :param <prio>: ship being docked priority
        """

        if prio == 0:
            self.n_ships_waiting -= 1
            self.ships_waiting.append((self.env.now, self.n_ships_waiting))
        else:
            self.n_special_ships_waiting -= 1
            self.special_ships_waiting.append((self.env.now, self.n_special_ships_waiting))

        self.n_tugs_in_use += 1
        self.tugs_in_use.append((self.env.now, self.n_tugs_in_use))

    def docking_completed(self):
        """Store the state changes due to the end of a ship docking.
        
        :param <prio>: ship docked priority
        """

        self.n_tugs_in_use -= 1
        self.tugs_in_use.append((self.env.now, self.n_tugs_in_use))

        self.n_docks_in_use += 1
        self.docks_in_use.append((self.env.now, self.n_docks_in_use))

        self.n_ships_docked += 1
        self.ships_docked.append((self.env.now, self.n_ships_docked))

        self.n_ships_waiting_bunkering += 1
        self.ships_waiting_bunkering.append((self.env.now, self.n_ships_waiting_bunkering))

    def start_bunkering(self):
        """Store the state changes due to the beginning of a ship bunkering."""

        self.n_ships_waiting_bunkering -= 1
        self.ships_waiting_bunkering.append((self.env.now, self.n_ships_waiting_bunkering))

        self.n_ships_bunkering += 1
        self.ships_bunkering.append((self.env.now, self.n_ships_bunkering))

        self.n_barges_in_use += 1
        self.barges_in_use.append((self.env.now, self.n_barges_in_use))

    def bunkering_completed(self):
        """Store the state changes due to the end of a ship bunkering."""

        self.n_ships_bunkering -= 1
        self.ships_bunkering.append((self.env.now, self.n_ships_bunkering))

        self.n_barges_in_use -=1
        self.barges_in_use.append((self.env.now, self.n_barges_in_use))

    def start_maintenance(self):
        """Store the state changes due to the beginning of a tug maintenance."""

        self.n_tugs_in_maintenance += 1
        self.tugs_in_maintenance.append((self.env.now, self.n_tugs_in_maintenance))

    def maintenance_completed(self):
        """Store the state changes due to the end of a ship maintenance."""

        self.n_tugs_in_maintenance -= 1
        self.tugs_in_maintenance.append((self.env.now, self.n_tugs_in_maintenance))

    def ship_supplied(self):
        """Store the state changes due to the beginning of a un-docking procedure.
        """

        self.n_docks_in_use -= 1
        self.docks_in_use.append((self.env.now, self.n_docks_in_use))

        self.n_ships_docked -= 1
        self.ships_docked.append((self.env.now, self.n_ships_docked))

        self.n_ships_supplied += 1
        self.ships_supplied.append((self.env.now, self.n_ships_supplied))

    def tug_locked(self):
        """Store the state changes due to the lock of a (resource) tug."""

        self.n_tugs_in_use += 1
        self.tugs_in_use.append((self.env.now, self.n_tugs_in_use))

    def tug_released(self):
        """Store the state changes due to the release of a (resource) tug."""

        self.n_tugs_in_use -= 1
        self.tugs_in_use.append((self.env.now, self.n_tugs_in_use))

    def ship_exited(self):
        """Store the state changes due to the exit of a ship from the system."""

        self.n_ships_system -= 1
        self.ships_system.append((self.env.now, self.n_ships_system))

    def plot_arrivals(self):
        """Plot results related to Arrivals sub-system."""

        # Plot arrivals

        x, y = list(zip(*self.ships_system))
        plt.plot(x, y, label='# of ships in the system')

        x, y = list(zip(*self.ships_waiting))
        plt.plot(x, y, label='# of ships waiting')

        x, y = list(zip(*self.special_ships_waiting))
        plt.plot(x, y, label='# of special ships waiting')

        x, y = list(zip(*self.tugs_in_use))
        plt.plot(x, y, label='# of tugs in use')

        x, y = list(zip(*self.docks_in_use))
        plt.plot(x, y, label='# docks in use')

        #x, y = list(zip(*self.ships_supplied))
        #plt.plot(x, y, label='# of ships served')

        #x, y = list(zip(*self.tugs_in_maintenance))
        #plt.plot(x, y, label='# of tugs in maintenance')

        plt.title('Arrivals situation')
        plt.xlabel('Time step')
        plt.legend()
        plt.grid(True, linestyle='--')
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        plt.savefig(f'{PLOTS_PATH}arrivals_{self.sim_docks}_{self.sim_tugs}_{self.sim_barges}')
        plt.clf()

        
        # Plot tugs maintenance

        x, y = list(zip(*self.tugs_in_maintenance))
        plt.plot(x, y, label='# of tugs in maintenance', color='grey')

        plt.title('Tugs maintenance')
        plt.xlabel('Time step')
        plt.legend()
        plt.grid(True, linestyle='--')
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        plt.savefig(f'{PLOTS_PATH}tugs_{self.sim_docks}_{self.sim_tugs}_{self.sim_barges}')
        plt.clf()

    def plot_dockings(self):
        """Plot results related to Docks sub-systen."""

        # Plot docks

        x, y = list(zip(*self.ships_docked))
        plt.plot(x, y, label='# of ships docked')

        x, y = list(zip(*self.ships_waiting_bunkering))
        plt.plot(x, y, label='# of ships waiting bunkering')

        x, y = list(zip(*self.ships_bunkering))
        plt.plot(x, y, label='# of ships bunkering')

        x, y = list(zip(*self.barges_in_use))
        plt.plot(x, y, label='# of fuel barges in use')

        plt.title('Docks situation')
        plt.xlabel('Time step')
        plt.legend()
        plt.grid(True, linestyle='--')
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        plt.savefig(f'{PLOTS_PATH}docks_{self.sim_docks}_{self.sim_tugs}_{self.sim_barges}')
        plt.clf()

    def store_queues_times(self):
        """Stores in a log file min, max and avg. waiting time for each queue (Entrance, Bunkering, Exit).
        """
        
        # Store waiting times (min., max., avg.)

        # For entering the harbour
        min_val = min(self.entrance_queue)
        max_val = max(self.entrance_queue)
        avg = mean(self.entrance_queue)
        queues_logger.info(
            f'[ENTRANCE_WAIT]: Min.: {min_val}, Max.: {max_val}, Avg.: {avg}')

        # For bunkering
        min_val = min(self.bunkering_queue)
        max_val = max(self.bunkering_queue)
        avg = mean(self.bunkering_queue)
        queues_logger.info(
            f'[BUNKERING_WAIT]: Min.: {min_val}, Max.: {max_val}, Avg.: {avg}')

        # For exiting the harbour
        min_val = min(self.exit_queue)
        max_val = max(self.exit_queue)
        avg = mean(self.exit_queue)
        queues_logger.info(
            f'[EXIT_WAIT]: Min.: {min_val}, Max.: {max_val}, Avg.: {avg}')